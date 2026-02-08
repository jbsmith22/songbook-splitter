"""Fix syntax errors in the provenance viewer"""
import re

print('Fixing template literal syntax errors...')

# Read the file
with open('web/viewers/complete_provenance_viewer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the queueText mapping - replace actual newlines with \n
content = content.replace(
    '''const queueText = reprocessQueue.map((item, i) =>
                `${i+1}. ${item.source_pdf}
Book ID: ${item.book_id}
Added: ${new Date(item.added_at).toLocaleString()}`
            ).join('

');''',
    '''const queueText = reprocessQueue.map((item, i) =>
                `${i+1}. ${item.source_pdf}\\nBook ID: ${item.book_id}\\nAdded: ${new Date(item.added_at).toLocaleString()}`
            ).join('\\n\\n');'''
)

# Fix the confirm dialog
content = content.replace(
    '''if (confirm(`Reprocess Queue (${reprocessQueue.length} books):

${queueText}

Export to file?`)) {''',
    '''if (confirm(`Reprocess Queue (${reprocessQueue.length} books):\\n\\n${queueText}\\n\\nExport to file?`)) {'''
)

# Write back
with open('web/viewers/complete_provenance_viewer.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed!')
print('Replaced literal newlines in template strings with \\n escapes')
