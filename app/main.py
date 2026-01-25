"""
Main entry point for ECS containerized tasks.

This module serves as the dispatcher for different task types.
The TASK_TYPE environment variable determines which task to run.
"""

import os
import sys

# Add parent directory to path to import from ecs module
sys.path.insert(0, '/app')

from ecs.task_entrypoints import (
    toc_discovery_task,
    toc_parser_task,
    page_mapper_task,
    song_verifier_task,
    pdf_splitter_task,
    manifest_generator_task
)

if __name__ == '__main__':
    task_type = os.environ.get('TASK_TYPE')
    
    if task_type == 'toc_discovery':
        toc_discovery_task()
    elif task_type == 'toc_parser':
        toc_parser_task()
    elif task_type == 'page_mapper':
        page_mapper_task()
    elif task_type == 'song_verifier':
        song_verifier_task()
    elif task_type == 'pdf_splitter':
        pdf_splitter_task()
    elif task_type == 'manifest_generator':
        manifest_generator_task()
    else:
        print(f"ERROR: Unknown task type: {task_type}", file=sys.stderr)
        sys.exit(1)
