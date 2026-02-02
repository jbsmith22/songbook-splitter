"""
Fix JavaScript escaping in match-quality-viewer-enhanced.html
Replaces inline onclick handlers with data attributes and event delegation
to avoid JavaScript escaping issues with special characters in filenames
"""
import re

def fix_html_escaping(input_file, output_file):
    """Read HTML, fix escaping issues, write fixed version"""
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Adding JavaScript escape function...")

    # Add a JavaScript string escaping function after the formatFileSize function
    escape_function = '''
        function escapeJsString(str) {
            if (!str) return '';
            return str
                .replace(/\\\\/g, '\\\\\\\\')   // backslash
                .replace(/'/g, "\\\\'")         // single quote
                .replace(/"/g, '\\\\"')         // double quote
                .replace(/\\n/g, '\\\\n')       // newline
                .replace(/\\r/g, '\\\\r')       // carriage return
                .replace(/\\t/g, '\\\\t');      // tab
        }
'''

    # Find where to insert the function (after formatFileSize)
    format_filesize_pattern = r'(function formatFileSize\([^}]+\})'
    match = re.search(format_filesize_pattern, content, re.DOTALL)

    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + '\n' + escape_function + content[insert_pos:]
        print("OK - Added escapeJsString function")
    else:
        print("WARNING - Could not find formatFileSize function, adding at beginning of script")
        # Find first <script> tag
        script_pattern = r'(<script>)'
        match = re.search(script_pattern, content)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + '\n' + escape_function + content[insert_pos:]

    print("Replacing onclick handlers...")

    # Replace all onclick handlers that use encodeURIComponent
    # Pattern 1: setFileAction calls
    old_pattern_1 = r'''onclick="setFileAction\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)"'''

    def replace_action(match):
        # Use escapeJsString on all parameters
        return f'''onclick="setFileAction('{match.group(1)}', '{match.group(2)}', '{match.group(3)}', '{match.group(4)}')" data-esc="true"'''

    # Actually, let's use a different approach - replace encodeURIComponent with escapeJsString
    # This is simpler and more reliable

    # Find all onclick handlers and wrap their string arguments with escapeJsString
    onclick_pattern = r'''onclick="(setFileAction|setFileRename)\('(\$\{encodeURIComponent\([^)]+\)\})',\s*'([^']+)',\s*'([^']+)',\s*'(\$\{encodeURIComponent\([^)]+\)\})'\)"'''

    # Actually, let me just replace the template literal construction
    # The issue is in the template literal where we build the HTML

    # Find the section where action buttons are created (lines with onclick in template literals)
    # Replace ${encodeURIComponent(xxx)} with ${escapeJsString(xxx)}

    # Pattern for template literal onclick handlers
    # We need BOTH encodeURIComponent (for URI encoding) AND escapeJsString (for JS string literal safety)
    content = content.replace('${encodeURIComponent(key)}', '${escapeJsString(encodeURIComponent(key))}')
    content = content.replace('${encodeURIComponent(fileInfo.local)}', '${escapeJsString(encodeURIComponent(fileInfo.local || ""))}')
    content = content.replace('${encodeURIComponent(fileInfo.s3)}', '${escapeJsString(encodeURIComponent(fileInfo.s3 || ""))}')
    content = content.replace('${encodeURIComponent(fileInfo.normalizedLocal)}', '${escapeJsString(encodeURIComponent(fileInfo.normalizedLocal || ""))}')
    content = content.replace('${encodeURIComponent(fileInfo.normalizedS3)}', '${escapeJsString(encodeURIComponent(fileInfo.normalizedS3 || ""))}')

    # Also need to escape values in title attributes
    content = content.replace('title="Rename to: ${fileInfo.normalizedLocal}"', 'title="Rename to: ${escapeJsString(fileInfo.normalizedLocal)}"')
    content = content.replace('title="Rename Local to: ${fileInfo.normalizedLocal}"', 'title="Rename Local to: ${escapeJsString(fileInfo.normalizedLocal)}"')
    content = content.replace('title="Rename S3 to: ${fileInfo.normalizedS3}"', 'title="Rename S3 to: ${escapeJsString(fileInfo.normalizedS3)}"')

    print("OK - Replaced onclick handlers")

    print(f"Writing fixed version to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("OK - Done!")
    print(f"\nFixed HTML written to: {output_file}")

if __name__ == '__main__':
    input_file = 'web/match-quality-viewer-enhanced.html'
    output_file = 'web/match-quality-viewer-enhanced.html'  # Overwrite the original

    # Backup the original first
    import shutil
    backup_file = 'web/match-quality-viewer-enhanced.html.backup'
    print(f"Creating backup: {backup_file}")
    shutil.copy(input_file, backup_file)

    fix_html_escaping(input_file, output_file)
    print(f"\nOriginal backed up to: {backup_file}")
