"""
Deploy updated Step Functions state machine definition

This updates the state machine to pass force_reprocess to the CheckProcessed Lambda.
"""
import boto3
import json
from pathlib import Path

STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
DEFINITION_FILE = 'infra/step_functions_state_machine.json'

def load_and_substitute_arns(definition_path):
    """Load the definition and substitute placeholder ARNs"""
    with open(definition_path, 'r') as f:
        definition = f.read()

    # Get current state machine to extract ARNs
    sfn = boto3.client('stepfunctions')
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)

    # Parse the current definition to extract ARN values
    current_def = json.loads(response['definition'])

    # Extract ARNs from current definition (simplified - just for the Lambda)
    check_processed_arn = current_def['States']['CheckAlreadyProcessed']['Parameters']['FunctionName']
    record_start_arn = current_def['States']['RecordProcessingStart']['Parameters']['FunctionName']

    # For now, just use the values from the AWS deployment
    # In a real setup, these would come from a config file or environment variables
    substitutions = {
        '${CheckProcessedLambdaArn}': check_processed_arn,
        '${RecordStartLambdaArn}': record_start_arn,
        # Add more as needed - for now we're only updating the CheckProcessed step
    }

    for placeholder, value in substitutions.items():
        definition = definition.replace(placeholder, value)

    return definition

def deploy_state_machine(definition):
    """Deploy the updated definition"""
    sfn = boto3.client('stepfunctions')

    print('Deploying updated state machine definition...')
    print(f'State Machine: {STATE_MACHINE_ARN}')
    print()

    # Validate JSON
    try:
        json.loads(definition)
        print('✓ Definition JSON is valid')
    except json.JSONDecodeError as e:
        print(f'✗ Invalid JSON: {e}')
        return False

    # Update the state machine
    try:
        response = sfn.update_state_machine(
            stateMachineArn=STATE_MACHINE_ARN,
            definition=definition
        )

        print(f'✓ State machine updated successfully')
        print(f'  Update Date: {response["updateDate"]}')
        return True

    except Exception as e:
        print(f'✗ Error updating state machine: {e}')
        return False

if __name__ == '__main__':
    print('='*80)
    print('DEPLOYING STATE MACHINE: CheckProcessed with force_reprocess support')
    print('='*80)
    print()

    # Check if we can just update the definition directly with a simpler approach
    print('Using simplified deployment: updating just the CheckProcessed step...')
    print()

    sfn = boto3.client('stepfunctions')

    # Get current definition
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)
    current_def = json.loads(response['definition'])

    # Update the CheckProcessed Payload
    if 'States' in current_def and 'CheckAlreadyProcessed' in current_def['States']:
        check_step = current_def['States']['CheckAlreadyProcessed']
        if 'Parameters' in check_step and 'Payload' in check_step['Parameters']:
            # Add force_reprocess to payload
            check_step['Parameters']['Payload']['force_reprocess.$'] = '$.force_reprocess'

            print('Updated CheckAlreadyProcessed step:')
            print(json.dumps(check_step['Parameters']['Payload'], indent=2))
            print()

            # Deploy
            new_definition = json.dumps(current_def)
            response = sfn.update_state_machine(
                stateMachineArn=STATE_MACHINE_ARN,
                definition=new_definition
            )

            print('='*80)
            print('DEPLOYMENT COMPLETE')
            print('='*80)
            print(f'Updated: {response["updateDate"]}')
            print()
            print('The state machine now passes force_reprocess to the Lambda!')
            print('Try clicking "Reprocess" again - it should actually work now.')
        else:
            print('Error: Could not find Payload in state machine definition')
    else:
        print('Error: Could not find CheckAlreadyProcessed state')
