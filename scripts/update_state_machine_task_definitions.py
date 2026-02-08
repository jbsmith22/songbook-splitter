"""
Update Step Functions state machine to use latest ECS task definitions

This fixes the Docker image pull issue by using :latest tag instead of pinned SHA256.
"""
import boto3
import json

STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'

# Task definition families to update
TASK_FAMILIES = [
    'jsmith-toc-discovery',
    'jsmith-toc-parser',
    'jsmith-page-mapper',
    'jsmith-song-verifier',
    'jsmith-pdf-splitter'
]

def get_latest_task_definition(family):
    """Get the latest ACTIVE task definition ARN for a family"""
    ecs = boto3.client('ecs')
    response = ecs.list_task_definitions(
        familyPrefix=family,
        status='ACTIVE',
        sort='DESC',
        maxResults=1
    )
    if response['taskDefinitionArns']:
        return response['taskDefinitionArns'][0]
    return None

def update_state_machine():
    """Update state machine with latest task definitions"""
    sfn = boto3.client('stepfunctions')

    # Get current state machine definition
    response = sfn.describe_state_machine(stateMachineArn=STATE_MACHINE_ARN)
    definition = json.loads(response['definition'])

    print('Current task definitions in state machine:')
    print()

    # Update TOCDiscovery
    old_toc_discovery = definition['States']['TOCDiscovery']['Parameters']['TaskDefinition']
    new_toc_discovery = get_latest_task_definition('jsmith-toc-discovery')
    if new_toc_discovery:
        definition['States']['TOCDiscovery']['Parameters']['TaskDefinition'] = new_toc_discovery
        print(f'TOCDiscovery: {old_toc_discovery} -> {new_toc_discovery}')

    # Update TOCParsing
    old_toc_parsing = definition['States']['TOCParsing']['Parameters']['TaskDefinition']
    new_toc_parsing = get_latest_task_definition('jsmith-toc-parser')
    if new_toc_parsing:
        definition['States']['TOCParsing']['Parameters']['TaskDefinition'] = new_toc_parsing
        print(f'TOCParsing: {old_toc_parsing} -> {new_toc_parsing}')

    # Update PageMapping (if exists)
    if 'PageMapping' in definition['States'] and 'TaskDefinition' in definition['States']['PageMapping']['Parameters']:
        old_page_mapping = definition['States']['PageMapping']['Parameters']['TaskDefinition']
        new_page_mapping = get_latest_task_definition('jsmith-page-mapper')
        if new_page_mapping:
            definition['States']['PageMapping']['Parameters']['TaskDefinition'] = new_page_mapping
            print(f'PageMapping: {old_page_mapping} -> {new_page_mapping}')

    # Update SongVerification (if exists)
    if 'SongVerification' in definition['States'] and 'TaskDefinition' in definition['States']['SongVerification']['Parameters']:
        old_verification = definition['States']['SongVerification']['Parameters']['TaskDefinition']
        new_verification = get_latest_task_definition('jsmith-song-verifier')
        if new_verification:
            definition['States']['SongVerification']['Parameters']['TaskDefinition'] = new_verification
            print(f'SongVerification: {old_verification} -> {new_verification}')

    # Update PDFSplitting (if exists)
    if 'PDFSplitting' in definition['States'] and 'TaskDefinition' in definition['States']['PDFSplitting']['Parameters']:
        old_splitting = definition['States']['PDFSplitting']['Parameters']['TaskDefinition']
        new_splitting = get_latest_task_definition('jsmith-pdf-splitter')
        if new_splitting:
            definition['States']['PDFSplitting']['Parameters']['TaskDefinition'] = new_splitting
            print(f'PDFSplitting: {old_splitting} -> {new_splitting}')

    print()
    print('Updating state machine...')

    # Update the state machine
    response = sfn.update_state_machine(
        stateMachineArn=STATE_MACHINE_ARN,
        definition=json.dumps(definition)
    )

    print(f'State machine updated: {response["updateDate"]}')
    print()
    print('The state machine now uses the latest task definitions with :latest tags.')

if __name__ == '__main__':
    print('='*80)
    print('UPDATING STATE MACHINE TASK DEFINITIONS')
    print('='*80)
    print()

    update_state_machine()

    print()
    print('='*80)
    print('UPDATE COMPLETE')
    print('='*80)
    print()
    print('Try reprocessing again - it should work now!')
