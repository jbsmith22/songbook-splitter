"""
Deploy Page Analysis feature to the pipeline

This script:
1. Creates an ECS task definition for page-analysis
2. Updates the Step Functions state machine to include the PageAnalysis step

Run this after pushing the updated Docker image to ECR.
"""
import boto3
import json
import sys

# Configuration
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
ECR_REPO = '227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter'
CLUSTER_ARN = 'jsmith-sheetmusic-splitter-cluster'  # Just the cluster name, not full ARN
# Use the same roles as other ECS tasks (required by Step Functions IAM policy)
EXECUTION_ROLE_ARN = 'arn:aws:iam::227027150061:role/jsmith-sheetmusic-splitter-ECSTaskExecutionRole-lk6cYO4BePSL'
TASK_ROLE_ARN = 'arn:aws:iam::227027150061:role/jsmith-sheetmusic-splitter-ECSTaskRole-w6lDb4md62rc'
OUTPUT_BUCKET = 'jsmith-output'

# Network config (get from existing task)
SUBNETS = None  # Will be extracted from existing state machine
SECURITY_GROUPS = None


def get_network_config_from_existing():
    """Extract network config from existing state machine definition"""
    global SUBNETS, SECURITY_GROUPS

    sfn = boto3.client('stepfunctions')
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)
    definition = json.loads(response['definition'])

    # Get from TOCDiscovery step
    toc_step = definition['States']['TOCDiscovery']['Parameters']
    network_config = toc_step['NetworkConfiguration']['AwsvpcConfiguration']

    SUBNETS = network_config['Subnets']
    SECURITY_GROUPS = network_config['SecurityGroups']

    print(f'Network config extracted:')
    print(f'  Subnets: {SUBNETS}')
    print(f'  Security Groups: {SECURITY_GROUPS}')
    print()


def create_page_analysis_task_definition():
    """Create ECS task definition for page-analysis"""
    ecs = boto3.client('ecs')

    # Check if task definition already exists
    try:
        response = ecs.describe_task_definition(taskDefinition='jsmith-page-analysis')
        print(f'Task definition already exists: {response["taskDefinition"]["taskDefinitionArn"]}')
        return response['taskDefinition']['taskDefinitionArn']
    except ecs.exceptions.ClientException:
        pass  # Task definition doesn't exist, create it

    print('Creating ECS task definition for page-analysis...')

    task_def = {
        'family': 'jsmith-page-analysis',
        'networkMode': 'awsvpc',
        'requiresCompatibilities': ['FARGATE'],
        'cpu': '1024',  # 1 vCPU
        'memory': '4096',  # 4 GB - need memory for PDF rendering + Bedrock
        'executionRoleArn': EXECUTION_ROLE_ARN,
        'taskRoleArn': TASK_ROLE_ARN,
        'containerDefinitions': [
            {
                'name': 'page-analysis',
                'image': f'{ECR_REPO}:latest',
                'essential': True,
                'environment': [
                    {'name': 'TASK_TYPE', 'value': 'page_analysis'},
                    {'name': 'OUTPUT_BUCKET', 'value': OUTPUT_BUCKET},
                    {'name': 'AWS_DEFAULT_REGION', 'value': 'us-east-1'}
                ],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': '/aws/ecs/jsmith-sheetmusic-splitter',  # Must match other tasks
                        'awslogs-region': 'us-east-1',
                        'awslogs-stream-prefix': 'page-analysis'
                    }
                }
            }
        ]
    }

    response = ecs.register_task_definition(**task_def)
    task_def_arn = response['taskDefinition']['taskDefinitionArn']

    print(f'Created task definition: {task_def_arn}')
    return task_def_arn


def update_state_machine_with_page_analysis(task_def_arn):
    """Update state machine to include PageAnalysis step"""
    sfn = boto3.client('stepfunctions')

    # Get current state machine definition
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)
    definition = json.loads(response['definition'])

    # Find what transitions TO PageMapping and update it to go to PageAnalysis
    # The deployed state machine has: TOCParsing -> PageMapping
    # We want: TOCParsing -> PageAnalysis -> PageMapping

    # Check for ValidateTOC first (in case it exists)
    if 'ValidateTOC' in definition['States']:
        old_default = definition['States']['ValidateTOC'].get('Default', 'N/A')
        if old_default != 'PageAnalysis':
            definition['States']['ValidateTOC']['Default'] = 'PageAnalysis'
            print(f'Updated ValidateTOC.Default: {old_default} -> PageAnalysis')
        else:
            print(f'ValidateTOC.Default already points to PageAnalysis')
    elif 'TOCParsing' in definition['States']:
        # No ValidateTOC - update TOCParsing.Next instead
        old_next = definition['States']['TOCParsing'].get('Next', 'N/A')
        if old_next == 'PageMapping':
            definition['States']['TOCParsing']['Next'] = 'PageAnalysis'
            print(f'Updated TOCParsing.Next: {old_next} -> PageAnalysis')
        elif old_next == 'PageAnalysis':
            print(f'TOCParsing.Next already points to PageAnalysis')
        else:
            print(f'WARNING: TOCParsing.Next is {old_next}, not PageMapping. Manual intervention needed.')

    # Check if PageAnalysis already exists
    if 'PageAnalysis' in definition['States']:
        print('PageAnalysis step already exists in state machine')

        # Update the task definition ARN
        definition['States']['PageAnalysis']['Parameters']['TaskDefinition'] = task_def_arn
        print(f'Updated task definition to: {task_def_arn}')
    else:
        print('Adding PageAnalysis step to state machine...')

        # Add PageAnalysis step
        definition['States']['PageAnalysis'] = {
            'Type': 'Task',
            'Resource': 'arn:aws:states:::ecs:runTask.sync',
            'Parameters': {
                'LaunchType': 'FARGATE',
                'Cluster': CLUSTER_ARN,
                'TaskDefinition': task_def_arn,
                'NetworkConfiguration': {
                    'AwsvpcConfiguration': {
                        'Subnets': SUBNETS,
                        'SecurityGroups': SECURITY_GROUPS,
                        'AssignPublicIp': 'ENABLED'
                    }
                },
                'Overrides': {
                    'ContainerOverrides': [
                        {
                            'Name': 'page-analysis',
                            'Environment': [
                                {'Name': 'TASK_TYPE', 'Value': 'page_analysis'},
                                {'Name': 'BOOK_ID', 'Value.$': '$.book_id'},
                                {'Name': 'SOURCE_PDF_URI', 'Value.$': '$.source_pdf_uri'},
                                {'Name': 'ARTIST', 'Value.$': '$.artist'},
                                {'Name': 'BOOK_NAME', 'Value.$': '$.book_name'},
                                {'Name': 'OUTPUT_BUCKET', 'Value': OUTPUT_BUCKET}
                            ]
                        }
                    ]
                }
            },
            'ResultPath': '$.page_analysis',
            'Next': 'PageMapping',
            'Retry': [
                {
                    'ErrorEquals': ['States.TaskFailed'],
                    'IntervalSeconds': 30,
                    'MaxAttempts': 2,
                    'BackoffRate': 2.0
                }
            ],
            'Catch': [
                {
                    'ErrorEquals': ['States.ALL'],
                    'ResultPath': '$.page_analysis_error',
                    'Next': 'PageMapping',
                    'Comment': 'Continue without page analysis if it fails'
                }
            ]
        }

    # Update the state machine
    print('Updating state machine...')
    response = sfn.update_state_machine(
        stateMachineArn=STATE_MACHINE_ARN,
        definition=json.dumps(definition)
    )

    print(f'State machine updated: {response["updateDate"]}')
    return True


def verify_deployment():
    """Verify the deployment"""
    sfn = boto3.client('stepfunctions')
    ecs = boto3.client('ecs')

    print()
    print('Verifying deployment...')
    print()

    # Check task definition
    try:
        response = ecs.describe_task_definition(taskDefinition='jsmith-page-analysis')
        print(f'[OK] Task definition exists: {response["taskDefinition"]["taskDefinitionArn"]}')
    except Exception as e:
        print(f'[FAIL] Task definition error: {e}')

    # Check state machine
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)
    definition = json.loads(response['definition'])

    if 'PageAnalysis' in definition['States']:
        print(f'[OK] PageAnalysis step exists in state machine')
        task_def = definition['States']['PageAnalysis']['Parameters'].get('TaskDefinition', 'N/A')
        print(f'  Task Definition: {task_def}')
    else:
        print(f'[FAIL] PageAnalysis step not found in state machine')

    # Check routing to PageAnalysis
    if 'TOCParsing' in definition['States']:
        next_state = definition['States']['TOCParsing'].get('Next', 'N/A')
        print(f'[OK] TOCParsing.Next = {next_state}')


def main():
    print('=' * 80)
    print('DEPLOYING PAGE ANALYSIS FEATURE')
    print('=' * 80)
    print()

    # Step 1: Get network config from existing state machine
    print('Step 1: Extracting network configuration...')
    get_network_config_from_existing()

    # Step 2: Create ECS task definition
    print('Step 2: Creating/updating ECS task definition...')
    task_def_arn = create_page_analysis_task_definition()
    print()

    # Step 3: Update state machine
    print('Step 3: Updating state machine...')
    update_state_machine_with_page_analysis(task_def_arn)
    print()

    # Step 4: Verify
    print('Step 4: Verifying deployment...')
    verify_deployment()

    print()
    print('=' * 80)
    print('DEPLOYMENT COMPLETE')
    print('=' * 80)
    print()
    print('The pipeline now includes the PageAnalysis step!')
    print()
    print('To test:')
    print('  1. Reprocess a book using the viewer')
    print('  2. Check for page_analysis.json in S3 artifacts')
    print('  3. The manual split editor will auto-load the pre-calculated offset')


if __name__ == '__main__':
    main()
