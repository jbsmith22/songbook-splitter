"""
Render S3 inventory CSV as a hierarchical HTML tree.
"""
import csv
from collections import defaultdict

def build_tree(objects):
    """Build a nested tree structure from flat object list."""
    tree = {}
    
    for obj in objects:
        path = obj['full_path']
        parts = path.split('/')
        
        current = tree
        for i, part in enumerate(parts):
            is_file = (i == len(parts) - 1)
            
            if part not in current:
                if is_file:
                    current[part] = {
                        '_is_file': True,
                        '_size_mb': obj['size_mb'],
                        '_depth': obj['depth'],
                        '_full_path': path
                    }
                else:
                    current[part] = {
                        '_is_file': False,
                        '_size_mb': 0,
                        '_depth': 0,
                        '_full_path': None
                    }
            
            if not is_file:
                current = current[part]
    
    return tree

def render_tree_html(tree, level=0):
    """Recursively render tree as HTML."""
    html = []
    
    # Get only non-metadata items
    items = [(k, v) for k, v in tree.items() if not k.startswith('_')]
    
    # Sort: folders first, then files
    items = sorted(items, key=lambda x: (x[1].get('_is_file', False), x[0]))
    
    for name, node in items:
        is_file = node.get('_is_file', False)
        
        if is_file:
            size_mb = node.get('_size_mb', 0)
            depth = node.get('_depth', 0)
            
            # Color code by depth
            if depth == 3:
                color_class = 'depth-3'  # Correct
            elif depth == 4:
                color_class = 'depth-4'  # Needs fixing
            else:
                color_class = 'depth-other'  # Error
            
            html.append(f'<li class="file {color_class}">')
            html.append(f'<span class="file-icon">📄</span>')
            html.append(f'<span class="file-name">{name}</span>')
            html.append(f'<span class="file-size">({size_mb} MB)</span>')
            html.append('</li>')
        else:
            # Count children (non-metadata keys)
            children = [(k, v) for k, v in node.items() if not k.startswith('_')]
            file_count = sum(1 for k, v in children if v.get('_is_file', False))
            folder_count = sum(1 for k, v in children if not v.get('_is_file', False))
            
            html.append('<li class="folder">')
            html.append(f'<span class="folder-toggle" onclick="toggleFolder(this)">▶</span>')
            html.append(f'<span class="folder-icon">📁</span>')
            html.append(f'<span class="folder-name">{name}</span>')
            html.append(f'<span class="folder-count">({file_count} files, {folder_count} folders)</span>')
            html.append('<ul class="nested">')
            html.append(render_tree_html(node, level + 1))
            html.append('</ul>')
            html.append('</li>')
    
    return '\n'.join(html)

def main():
    print("📄 Reading S3 inventory CSV...")
    
    objects = []
    with open('s3_complete_inventory.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['depth'] = int(row['depth'])
            row['size_mb'] = float(row['size_mb'])
            objects.append(row)
    
    print(f"   Loaded {len(objects)} objects")
    
    print("🌳 Building tree structure...")
    tree = build_tree(objects)
    
    print("🎨 Rendering HTML...")
    tree_html = render_tree_html(tree)
    
    # Count statistics
    depth_3 = sum(1 for obj in objects if obj['depth'] == 3 and obj['is_pdf'] == 'True')
    depth_4 = sum(1 for obj in objects if obj['depth'] == 4 and obj['is_pdf'] == 'True')
    depth_other = sum(1 for obj in objects if obj['depth'] not in [3, 4] and obj['is_pdf'] == 'True')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 Bucket Tree - jsmith-output</title>
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
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }}
        
        .stat {{
            padding: 10px 15px;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .stat.correct {{
            background: #d4edda;
            color: #155724;
        }}
        
        .stat.needs-fix {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .stat.error {{
            background: #f8d7da;
            color: #721c24;
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
        
        .tree-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .nested {{
            display: none;
            padding-left: 30px;
        }}
        
        .nested.active {{
            display: block;
        }}
        
        li {{
            padding: 5px 0;
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
        
        .folder-name {{
            font-weight: 600;
            color: #333;
        }}
        
        .file-name {{
            color: #555;
        }}
        
        .folder-count, .file-size {{
            color: #999;
            font-size: 12px;
            margin-left: 8px;
        }}
        
        .file.depth-3 {{
            background: #f0fff0;
        }}
        
        .file.depth-4 {{
            background: #fffef0;
        }}
        
        .file.depth-other {{
            background: #fff0f0;
        }}
        
        .legend {{
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 13px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 12px;
            margin-right: 5px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>S3 Bucket Tree: jsmith-output</h1>
        <p>Complete hierarchical view of all folders and files</p>
        
        <div class="stats">
            <div class="stat correct">
                ✅ Correct Structure: {depth_3:,} files (depth 3)
            </div>
            <div class="stat needs-fix">
                ⚠️ Needs Flattening: {depth_4:,} files (depth 4)
            </div>
            <div class="stat error">
                ❌ Deep Nesting: {depth_other:,} files (depth 5+)
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color" style="background: #f0fff0;"></span>
                Depth 3 (Correct: artist/book/file.pdf)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #fffef0;"></span>
                Depth 4 (Has extra folder like /Songs/)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #fff0f0;"></span>
                Depth 5+ (Deeply nested - error)
            </div>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button onclick="expandLevel(1)">Expand Level 1</button>
        <button onclick="expandLevel(2)">Expand Level 2</button>
        <button onclick="expandLevel(3)">Expand Level 3</button>
    </div>
    
    <div class="tree-container">
        <ul id="tree-root">
            {tree_html}
        </ul>
    </div>
    
    <script>
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
    </script>
</body>
</html>'''
    
    output_file = 's3_tree_view.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML tree view created: {output_file}")
    print(f"\n📊 Statistics:")
    print(f"   Correct (depth 3): {depth_3:,} files")
    print(f"   Needs fixing (depth 4): {depth_4:,} files")
    print(f"   Errors (depth 5+): {depth_other:,} files")

if __name__ == '__main__':
    main()
