#!/usr/bin/env python3
"""
Create execution inputs for missing Billy Joel books and run them through the pipeline.
"""
import json
import boto3
import time
from pathlib import Path

# Missing Billy Joel books
missing_books = [
    "Billy Joel - Anthology.pdf",
    "Billy Joel - Complete Vol  1.pdf",
    "Billy Joel - Fantasies & Delusions.pdf",
    "Billy Joel - Glass Houses.pdf",
    "Billy Joel - Greatest Hits.pdf",
    "Billy Joel - Keyboard Book.pdf"
]

def create_execution_input(book_name):
    """Create Step Functions execution input for a book."""
    # Remove .pdf extension and clean up name
    clean_name = book_name.replace('.pdf', '').replace('  ', ' ')
    
    return {
        "artist": "Billy Joel",
        "book_title": clean_name,
        "s3_input_key": f"SheetMusicIn/Billy Joel/Books/{book_name}",
        "s3_output_prefix": f"SheetMusicOut/Billy_Joel/{clean_name.replace(' ', '_')}"
    }

def start_execution(sf_client, state_machine_arn, execution_input, book_name):
    """Start a Step Functions execution."""
    execution_name = f"BillyJoel-{book_name.replace(' ', '-').replace('.pdf', '')}-{int(time.time())}"
    
    try:
        response = sf_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(execution_input)
        )
        return response['executionArn']
    except Exception as e:
        print(f"ERROR starting execution for {book_name}: {e}")
        return None

def main():
    print("Processing missing Billy Joel books...")
    print()
    
    # AWS configuration
    state_machine_arn = "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine"
    sf_client = boto3.client('stepfunctions', region_name='us-east-1')
    
    executions = []
    
    for book_name in missing_books:
        print(f"Starting execution for: {book_name}")
        
        execution_input = create_execution_input(book_name)
        
        # Save input to file for reference
        input_file = f"test-{book_name.replace('.pdf', '').replace(' ', '-').lower()}-input.json"
        with open(input_file, 'w') as f:
            json.dump(execution_input, f, indent=2)
        
        # Start execution
        execution_arn = start_execution(sf_client, state_machine_arn, execution_input, book_name)
        
        if execution_arn:
            executions.append({
                'book': book_name,
                'execution_arn': execution_arn
            })
            print(f"  Started: {execution_arn}")
        
        print()
        
        # Small delay between executions
        time.sleep(2)
    
    print("=" * 80)
    print(f"Started {len(executions)} executions")
    print("=" * 80)
    print()
    
    # Save execution ARNs
    with open('billy-joel-executions.json', 'w') as f:
        json.dump(executions, f, indent=2)
    
    print("Execution ARNs saved to: billy-joel-executions.json")
    print()
    print("Monitor executions with:")
    for exec_info in executions:
        print(f"  aws stepfunctions describe-execution --execution-arn \"{exec_info['execution_arn']}\"")

if __name__ == '__main__':
    main()
