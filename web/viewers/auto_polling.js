/**
 * Auto-Polling for Reprocessing Jobs
 * Include this script in the provenance viewer to enable automatic status updates
 */

// Track active reprocessing jobs
let activeReprocessing = new Map();
let pollingInterval = null;
const POLL_INTERVAL_MS = 30000; // 30 seconds

// Override the existing triggerReprocess function
const originalTriggerReprocess = window.triggerReprocess;

window.triggerReprocess = async function(bookId, sourcePdf) {
    if (!apiConnected) {
        alert('API server not connected. Start it with: py scripts/pipeline_api_server.py');
        return;
    }

    const confirmMsg = 'Reprocess ' + sourcePdf + '?\n\nThis will trigger the Step Functions pipeline.';
    if (!confirm(confirmMsg)) {
        return;
    }

    try {
        const payload = { book_id: bookId, source_pdf: sourcePdf, force: true };
        const response = await fetch(API_BASE_URL + '/reprocess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'started') {
            // Add to active reprocessing tracking
            activeReprocessing.set(bookId, {
                executionArn: data.execution_arn,
                sourcePdf: sourcePdf,
                startTime: new Date(),
                useManualSplits: data.use_manual_splits
            });

            // Start polling if not already running
            if (!pollingInterval) {
                startPolling();
            }

            // Update the book row to show processing status
            updateBookRowProcessing(bookId, true);

            let msg = 'Reprocessing started!\n\nWill auto-update when complete.';
            if (data.use_manual_splits) {
                msg += '\n\nUsing manual split points';
            }
            alert(msg);

            // Also update the status display
            updateStatusDisplay();
        } else {
            alert('Error starting reprocess: ' + data.message);
        }
    } catch (error) {
        alert('Error triggering reprocess: ' + error.message);
    }
};

function startPolling() {
    console.log('Starting auto-polling for reprocessing jobs');
    pollingInterval = setInterval(checkReprocessingStatus, POLL_INTERVAL_MS);
    updateStatusDisplay();
}

function stopPolling() {
    if (pollingInterval) {
        console.log('Stopping auto-polling');
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    updateStatusDisplay();
}

async function checkReprocessingStatus() {
    if (activeReprocessing.size === 0) {
        stopPolling();
        return;
    }

    console.log('Checking status of ' + activeReprocessing.size + ' active jobs');

    for (const [bookId, jobInfo] of activeReprocessing.entries()) {
        try {
            // Check DynamoDB status
            const response = await fetch(API_BASE_URL + '/status/' + bookId, { method: 'GET' });
            const data = await response.json();

            if (data.status === 'found') {
                const status = data.processing_status;

                // Check if completed or failed
                if (status === 'completed' || status === 'failed') {
                    console.log('Book ' + bookId + ' finished with status: ' + status);

                    // Remove from active tracking
                    activeReprocessing.delete(bookId);

                    // Update the book row
                    updateBookRowProcessing(bookId, false);

                    // Show notification
                    const duration = Math.round((new Date() - jobInfo.startTime) / 1000);
                    const msg = 'Reprocessing complete!\n\n' +
                        'Book: ' + jobInfo.sourcePdf + '\n' +
                        'Status: ' + status + '\n' +
                        'Songs: ' + data.songs_extracted + '\n' +
                        'Duration: ' + duration + 's\n\n' +
                        'Refresh the page to see updated data.';

                    // Use a notification if available, otherwise alert
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification('Reprocessing Complete', {
                            body: jobInfo.sourcePdf + ' - ' + status,
                            icon: status === 'completed' ? '✓' : '✗'
                        });
                    } else {
                        alert(msg);
                    }

                    // Auto-refresh the book data (if we implement this)
                    // For now, just update the status display
                    updateStatusDisplay();
                }
            }
        } catch (error) {
            console.error('Error checking status for ' + bookId + ':', error);
        }
    }

    // If no more active jobs, stop polling
    if (activeReprocessing.size === 0) {
        stopPolling();
    }
}

function updateBookRowProcessing(bookId, isProcessing) {
    // Find the book row by book ID
    const rows = document.querySelectorAll('#table-body tr');
    for (const row of rows) {
        const codeElement = row.querySelector('code');
        if (codeElement && codeElement.textContent === bookId) {
            if (isProcessing) {
                row.style.backgroundColor = '#FFF3E0';
                row.style.borderLeft = '4px solid #FF9800';

                // Add a processing indicator to the status cell
                const statusCell = row.cells[2];
                if (statusCell) {
                    const badge = statusCell.querySelector('.badge');
                    if (badge) {
                        badge.innerHTML = 'PROCESSING... ⏳';
                        badge.className = 'badge badge-incomplete';
                    }
                }
            } else {
                row.style.backgroundColor = '';
                row.style.borderLeft = '';
            }
            break;
        }
    }
}

function updateStatusDisplay() {
    const statusElement = document.getElementById('api-status-text');
    if (statusElement) {
        let text = 'Connected';
        if (activeReprocessing.size > 0) {
            text += ' - ' + activeReprocessing.size + ' processing';
        }
        if (pollingInterval) {
            text += ' (polling every 30s)';
        }
        statusElement.textContent = text;
    }
}

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Show active jobs on page load (in case page was refreshed)
window.addEventListener('load', function() {
    if (activeReprocessing.size > 0) {
        startPolling();
    }
});

console.log('Auto-polling module loaded');
