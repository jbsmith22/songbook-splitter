"""
Build an interactive HTML tree browser for S3 bucket with delete command generation.
"""
import boto3
import json
from collections import defaultdict

def build_tree_structure():
    """Build hierarchical tree structure from S3 bucket."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print(f"Scanning S3 bucket: {bucket}")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    tree = {}
    total_files = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            size = obj['Size']
            total_files += 1
            
            # Build tree structure
            parts = key.split('/')
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    is_file = (i == len(parts) - 1)
                    current[part] = {
                        '_type': 'file' if is_file else 'folder',
                        '_size': size if is_file else 0,
                        '_path': '/'.join(parts[:i+1])
                    }
                    if not is_file:
                        current[part]['_children'] = {}
                
                if i < len(parts) - 1:
                    current = current[part]['_children']
            
            if total_files % 1000 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\nTotal files: {total_files}")
    return tree, total_files

def tree_to_html_nodes(tree, level=0):
    """Convert tree structure to HTML list items."""
    html = []
    
    # Sort: folders first, then files
    items = sorted(tree.items(), key=lambda x: (x[1]['_type'] == 'file', x[0]))
    
    for name, node in items:
        if name.startswith('_'):
            continue
            
        is_file = node['_type'] == 'file'
        path = node['_path'].replace("'", "\\'")
        
        if is_file:
            size_mb = node['_size'] / (1024 * 1024)
            html.append(f'<li class="file" data-path="{path}">')
            html.append(f'<span class="file-icon">📄</span> {name} ')
            html.append(f'<span class="file-size">({size_mb:.2f} MB)</span>')
            html.append(f'<button class="delete-btn" onclick="deleteFile(\'{path}\')">🗑️ Delete</button>')
            html.append('</li>')
        else:
            # Count children
            children = node.get('_children', {})
            child_count = len([k for k in children.keys() if not k.startswith('_')])
            
            html.append(f'<li class="folder" data-path="{path}">')
            html.append(f'<span class="folder-toggle" onclick="toggleFolder(this)">▶</span>')
            html.append(f'<span class="folder-icon">📁</span> <strong>{name}</strong> ')
            html.append(f'<span class="item-count">({child_count} items)</span>')
            html.append(f'<button class="delete-btn delete-folder-btn" onclick="deleteFolder(\'{path}\')">🗑️ Delete Folder</button>')
            html.append(f'<ul class="nested">')
            html.extend(tree_to_html_nodes(children, level + 1))
            html.append('</ul>')
            html.append('</li>')
    
    return html

def generate_html(tree, total_files):
    """Generate complete HTML page."""
    html_nodes = tree_to_html_nodes(tree)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 Bucket Browser - Delete Tool</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        
        .header .stats {{
            color: #666;
            font-size: 14px;
        }}
        
        .header .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            color: #856404;
        }}
        
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .controls button {{
            padding: 8px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .controls button:hover {{
            background: #0056b3;
        }}
        
        .main-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .tree-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .commands-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }}
        
        .commands-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .commands-header h2 {{
            font-size: 18px;
            color: #333;
        }}
        
        .commands-list {{
            flex: 1;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: #f8f9fa;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        }}
        
        .command-item {{
            background: white;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 3px solid #dc3545;
        }}
        
        .command-item.folder {{
            border-left-color: #ff6b6b;
        }}
        
        .command-path {{
            color: #666;
            font-size: 11px;
            margin-bottom: 5px;
        }}
        
        .command-code {{
            color: #333;
            word-break: break-all;
        }}
        
        .empty-state {{
            text-align: center;
            color: #999;
            padding: 40px;
        }}
        
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        ul.nested {{
            display: none;
            padding-left: 25px;
        }}
        
        ul.nested.active {{
            display: block;
        }}
        
        li {{
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
            position: relative;
        }}
        
        li:hover {{
            background: #f8f9fa;
        }}
        
        .folder-toggle {{
            cursor: pointer;
            display: inline-block;
            width: 20px;
            user-select: none;
            transition: transform 0.2s;
        }}
        
        .folder-toggle.expanded {{
            transform: rotate(90deg);
        }}
        
        .folder-icon, .file-icon {{
            margin: 0 5px;
        }}
        
        .item-count {{
            color: #999;
            font-size: 12px;
            margin-left: 5px;
        }}
        
        .file-size {{
            color: #999;
            font-size: 12px;
            margin-left: 5px;
        }}
        
        .file {{
            color: #555;
        }}
        
        .folder {{
            color: #333;
        }}
        
        .search-box {{
            width: 300px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .delete-btn {{
            padding: 4px 8px;
            margin-left: 10px;
            border: none;
            border-radius: 4px;
            background: #dc3545;
            color: white;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        
        li:hover .delete-btn {{
            opacity: 1;
        }}
        
        .delete-btn:hover {{
            background: #c82333;
        }}
        
        .delete-folder-btn {{
            background: #ff6b6b;
        }}
        
        .delete-folder-btn:hover {{
            background: #ff5252;
        }}
        
        .action-buttons {{
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }}
        
        .action-buttons button {{
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .copy-btn {{
            background: #28a745;
            color: white;
        }}
        
        .copy-btn:hover {{
            background: #218838;
        }}
        
        .clear-btn {{
            background: #6c757d;
            color: white;
        }}
        
        .clear-btn:hover {{
            background: #5a6268;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 S3 Bucket Browser - Delete Tool</h1>
        <div class="stats">
            <strong>Bucket:</strong> jsmith-output<br>
            <strong>Total Files:</strong> {total_files:,}
        </div>
        <div class="warning">
            ⚠️ <strong>Warning:</strong> Click delete buttons to generate PowerShell commands. Review and run them manually.
        </div>
    </div>
    
    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button onclick="expandLevel(1)">Expand Level 1</button>
        <button onclick="expandLevel(2)">Expand Level 2</button>
        <input type="text" class="search-box" placeholder="Search folders/files..." onkeyup="searchTree(this.value)">
    </div>
    
    <div class="main-container">
        <div class="tree-container">
            <ul id="tree-root">
                {''.join(html_nodes)}
            </ul>
        </div>
        
        <div class="commands-container">
            <div class="commands-header">
                <h2>🗑️ Delete Commands (<span id="command-count">0</span>)</h2>
            </div>
            <div class="commands-list" id="commands-list">
                <div class="empty-state">
                    Click delete buttons to generate commands
                </div>
            </div>
            <div class="action-buttons">
                <button class="copy-btn" onclick="copyAllCommands()">📋 Copy All Commands</button>
                <button class="clear-btn" onclick="clearCommands()">🗑️ Clear All</button>
            </div>
        </div>
    </div>
    
    <script>
        let deleteCommands = [];
        
        function toggleFolder(element) {{
            element.classList.toggle('expanded');
            const nested = element.parentElement.querySelector('.nested');
            if (nested) {{
                nested.classList.toggle('active');
            }}
        }}
        
        function expandAll() {{
            document.querySelectorAll('.nested').forEach(el => {{
                el.classList.add('active');
            }});
            document.querySelectorAll('.folder-toggle').forEach(el => {{
                el.classList.add('expanded');
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.nested').forEach(el => {{
                el.classList.remove('active');
            }});
            document.querySelectorAll('.folder-toggle').forEach(el => {{
                el.classList.remove('expanded');
            }});
        }}
        
        function expandLevel(level) {{
            collapseAll();
            
            function expandToLevel(element, depth) {{
                if (depth >= level) return;
                
                const nested = element.querySelector(':scope > .nested');
                const toggle = element.querySelector(':scope > .folder-toggle');
                
                if (nested && toggle) {{
                    nested.classList.add('active');
                    toggle.classList.add('expanded');
                    
                    const childFolders = nested.querySelectorAll(':scope > .folder');
                    childFolders.forEach(child => {{
                        expandToLevel(child, depth + 1);
                    }});
                }}
            }}
            
            document.querySelectorAll('#tree-root > .folder').forEach(folder => {{
                expandToLevel(folder, 0);
            }});
        }}
        
        function searchTree(query) {{
            query = query.toLowerCase().trim();
            
            if (!query) {{
                document.querySelectorAll('li').forEach(el => {{
                    el.style.display = '';
                }});
                collapseAll();
                return;
            }}
            
            document.querySelectorAll('li').forEach(el => {{
                el.style.display = 'none';
            }});
            
            document.querySelectorAll('li').forEach(el => {{
                const text = el.textContent.toLowerCase();
                if (text.includes(query)) {{
                    let current = el;
                    while (current) {{
                        current.style.display = '';
                        
                        const parentUl = current.parentElement;
                        if (parentUl && parentUl.classList.contains('nested')) {{
                            parentUl.classList.add('active');
                            const parentLi = parentUl.parentElement;
                            if (parentLi) {{
                                const toggle = parentLi.querySelector(':scope > .folder-toggle');
                                if (toggle) {{
                                    toggle.classList.add('expanded');
                                }}
                            }}
                        }}
                        
                        current = current.parentElement?.closest('li');
                    }}
                }}
            }});
        }}
        
        function deleteFile(path) {{
            const command = `aws s3 rm "s3://jsmith-output/${{path}}"`;
            addCommand(path, command, false);
        }}
        
        function deleteFolder(path) {{
            const command = `aws s3 rm "s3://jsmith-output/${{path}}/" --recursive`;
            addCommand(path, command, true);
        }}
        
        function addCommand(path, command, isFolder) {{
            deleteCommands.push({{ path, command, isFolder }});
            updateCommandsList();
        }}
        
        function updateCommandsList() {{
            const list = document.getElementById('commands-list');
            const count = document.getElementById('command-count');
            
            count.textContent = deleteCommands.length;
            
            if (deleteCommands.length === 0) {{
                list.innerHTML = '<div class="empty-state">Click delete buttons to generate commands</div>';
                return;
            }}
            
            list.innerHTML = deleteCommands.map((cmd, index) => `
                <div class="command-item ${{cmd.isFolder ? 'folder' : ''}}">
                    <div class="command-path">${{cmd.isFolder ? '📁' : '📄'}} ${{cmd.path}}</div>
                    <div class="command-code">${{cmd.command}}</div>
                </div>
            `).join('');
        }}
        
        function copyAllCommands() {{
            const commands = deleteCommands.map(cmd => cmd.command).join('\\n');
            navigator.clipboard.writeText(commands).then(() => {{
                alert(`Copied ${{deleteCommands.length}} commands to clipboard!`);
            }});
        }}
        
        function clearCommands() {{
            if (confirm('Clear all delete commands?')) {{
                deleteCommands = [];
                updateCommandsList();
            }}
        }}
        
        // Initialize: collapse all on load
        collapseAll();
    </script>
</body>
</html>"""
    
    return html

def main():
    print("Building S3 tree structure...")
    tree, total_files = build_tree_structure()
    
    print("Generating HTML...")
    html = generate_html(tree, total_files)
    
    output_file = 's3_bucket_browser_delete.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Created {output_file}")
    print(f"   Open this file in your browser")
    print(f"   Click delete buttons to generate AWS CLI commands")
    print(f"   Copy and run the commands in PowerShell")

if __name__ == '__main__':
    main()
