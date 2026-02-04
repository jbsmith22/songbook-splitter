/**
 * Auto-Polling for Reprocessing Jobs
 * Include this script in the provenance viewer to enable automatic status updates
 */

// Track active reprocessing jobs
let activeReprocessing = new Map();
let pollingInterval = null;
const POLL_INTERVAL_MS = 5000; // 5 seconds for more responsive updates

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

            // Create and show progress tracker
            showProgressTracker(bookId, sourcePdf, data.execution_arn);

            let msg = 'Reprocessing started!\n\nProgress tracker opened in new section.';
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
            // Update progress tracker with detailed step information
            if (jobInfo.executionArn) {
                updateProgressTracker(bookId, jobInfo.executionArn);
            }

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

                    // Hide progress tracker
                    hideProgressTracker(bookId);

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
            text += ' (polling every 5s)';
        }
        statusElement.textContent = text;
    }
}

// ===== Progress Tracker Functions =====

function showProgressTracker(bookId, sourcePdf, executionArn) {
    // Create progress tracker container if it doesn't exist
    let container = document.getElementById('progress-tracker-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'progress-tracker-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1000; background: white; border: 2px solid #2196F3; border-radius: 8px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 400px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
        document.body.appendChild(container);
    }

    // Create progress tracker for this book
    const trackerId = 'progress-' + bookId;
    let tracker = document.getElementById(trackerId);

    if (!tracker) {
        tracker = document.createElement('div');
        tracker.id = trackerId;
        tracker.style.cssText = 'margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #e0e0e0;';
        container.appendChild(tracker);
    }

    tracker.innerHTML = `
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 600; font-size: 14px; color: #1976D2; margin-bottom: 4px;">
                ${sourcePdf}
            </div>
            <div style="font-size: 12px; color: #666;">
                Book ID: ${bookId}
            </div>
        </div>
        <div id="steps-${bookId}" style="font-size: 13px;">
            <div style="color: #666; font-style: italic;">Loading pipeline status...</div>
        </div>
    `;

    // Immediate first update
    updateProgressTracker(bookId, executionArn);
}

function hideProgressTracker(bookId) {
    const trackerId = 'progress-' + bookId;
    const tracker = document.getElementById(trackerId);
    if (tracker) {
        tracker.style.opacity = '0.5';
        setTimeout(() => tracker.remove(), 3000);
    }

    // Remove container if no more trackers
    const container = document.getElementById('progress-tracker-container');
    if (container && container.children.length === 0) {
        container.remove();
    }
}

async function updateProgressTracker(bookId, executionArn) {
    try {
        // Fetch detailed execution progress
        const encodedArn = encodeURIComponent(executionArn);
        const response = await fetch(API_BASE_URL + '/execution_progress/' + encodedArn);
        const data = await response.json();

        if (data.status === 'error') {
            console.error('Error fetching progress:', data.message);
            return;
        }

        const stepsContainer = document.getElementById('steps-' + bookId);
        if (!stepsContainer) return;

        // Build step display
        let html = '';
        for (const step of data.steps) {
            let icon, color, text;

            if (step.status === 'completed') {
                icon = '✓';
                color = '#4CAF50';
                text = step.name;
            } else if (step.status === 'running') {
                icon = '⏳';
                color = '#FF9800';
                text = step.name + ' (running...)';
            } else {
                icon = '○';
                color = '#999';
                text = step.name;
            }

            html += `
                <div style="display: flex; align-items: center; margin: 6px 0;">
                    <span style="color: ${color}; font-weight: bold; margin-right: 8px; min-width: 20px;">${icon}</span>
                    <span style="color: ${step.status === 'pending' ? '#999' : '#333'};">${text}</span>
                </div>
            `;
        }

        // Add execution status
        if (data.execution_status === 'RUNNING') {
            html += `<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                Current: ${data.current_step || 'Initializing...'}
            </div>`;
        }

        stepsContainer.innerHTML = html;

    } catch (error) {
        console.error('Error updating progress tracker:', error);
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
