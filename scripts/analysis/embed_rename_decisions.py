"""
Embed the auto_rename_decisions.json into the HTML viewer
so all rename actions appear pre-selected when the page loads
"""
import json

def embed_rename_decisions(html_file, decisions_file):
    """Load decisions and embed them into the HTML"""
    print(f"Loading decisions from {decisions_file}...")
    with open(decisions_file, 'r', encoding='utf-8') as f:
        decisions = json.load(f)

    print(f"Loaded {len(decisions)} folders with rename decisions")

    print(f"Reading HTML from {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find the loadDecisions function and modify it to include embedded decisions
    search_pattern = """        function loadDecisions() {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : {};
        }"""

    if search_pattern not in html_content:
        print("ERROR: Could not find loadDecisions function in HTML")
        return False

    # Create the replacement code that embeds our decisions
    decisions_json = json.dumps(decisions, indent=2)

    replacement = f"""        function loadDecisions() {{
            // Pre-loaded rename decisions
            const embeddedDecisions = {decisions_json};

            // Load from localStorage
            const stored = localStorage.getItem(STORAGE_KEY);
            let decisions = stored ? JSON.parse(stored) : {{}};

            // Merge embedded decisions (embedded takes precedence for file decisions)
            for (const [folderPath, folderData] of Object.entries(embeddedDecisions)) {{
                if (!decisions[folderPath]) {{
                    decisions[folderPath] = {{}};
                }}
                if (!decisions[folderPath].fileDecisions) {{
                    decisions[folderPath].fileDecisions = {{}};
                }}
                // Merge file decisions from embedded data
                Object.assign(decisions[folderPath].fileDecisions, folderData.fileDecisions);
            }}

            console.log('Loaded ' + Object.keys(embeddedDecisions).length + ' folders with pre-selected renames');
            return decisions;
        }}"""

    html_content = html_content.replace(search_pattern, replacement)

    print(f"Writing updated HTML to {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("OK - Done!")
    print(f"\nHTML updated with {len(decisions)} folders of pre-selected rename decisions")
    return True

if __name__ == '__main__':
    html_file = 'web/match-quality-viewer-enhanced.html'
    decisions_file = 'data/analysis/auto_rename_decisions.json'

    # Backup first
    import shutil
    backup_file = 'web/match-quality-viewer-enhanced.html.backup3'
    print(f"Creating backup: {backup_file}")
    shutil.copy(html_file, backup_file)

    success = embed_rename_decisions(html_file, decisions_file)

    if success:
        print(f"\nOriginal backed up to: {backup_file}")
        print("\nNow open the HTML viewer - all rename actions will be pre-selected!")
    else:
        print("\nFailed - restoring backup")
        shutil.copy(backup_file, html_file)
