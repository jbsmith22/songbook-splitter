#!/usr/bin/env python3
"""
Generate HTML review page from verification results.
"""

import json
from pathlib import Path
import base64

def generate_html(results_file: Path, output_file: Path):
    """Generate HTML review page."""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Filter to only flagged PDFs
    flagged = [r for r in results if not r['passed']]
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Verification Review</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        .stat {
            padding: 10px 20px;
            background: #e3f2fd;
            border-radius: 4px;
        }
        .pdf-card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .pdf-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        .pdf-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .pdf-path {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .issues {
            background: #fff3e0;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .issue-item {
            color: #e65100;
            font-weight: 500;
            margin: 5px 0;
        }
        .pages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .page-card {
            border: 2px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px;
            background: #fafafa;
        }
        .page-card.flagged {
            border-color: #ff9800;
            background: #fff8e1;
        }
        .page-header {
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .page-image {
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .bedrock-response {
            font-size: 13px;
            color: #555;
            padding: 8px;
            background: white;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .review-buttons {
            display: flex;
            gap: 10px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 4px;
        }
        .btn {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-correct {
            background: #4caf50;
            color: white;
        }
        .btn-correct:hover {
            background: #45a049;
        }
        .btn-incorrect {
            background: #f44336;
            color: white;
        }
        .btn-incorrect:hover {
            background: #da190b;
        }
        .btn-skip {
            background: #9e9e9e;
            color: white;
        }
        .btn-skip:hover {
            background: #757575;
        }
        .reviewed {
            opacity: 0.6;
        }
        .review-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-correct {
            background: #c8e6c9;
            color: #2e7d32;
        }
        .status-incorrect {
            background: #ffcdd2;
            color: #c62828;
        }
        .status-skip {
            background: #e0e0e0;
            color: #616161;
        }
        .progress {
            background: #e0e0e0;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-bar {
            background: #4caf50;
            height: 100%;
            transition: width 0.3s;
        }
        .feedback-section {
            margin-top: 15px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        .feedback-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .feedback-options {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .feedback-btn {
            padding: 6px 12px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }
        .feedback-btn:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        .feedback-btn.selected {
            background: #2196f3;
            color: white;
            border-color: #2196f3;
        }
        .notes-input {
            width: 100%;
            margin-top: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: Arial, sans-serif;
            font-size: 13px;
            resize: vertical;
            min-height: 60px;
        }
        .btn-clear {
            background: #ff9800;
            color: white;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }
        .btn-clear:hover {
            background: #f57c00;
        }
        .split-section {
            margin-top: 15px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 4px;
            border: 2px solid #4caf50;
        }
        .split-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2e7d32;
        }
        .split-input {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #4caf50;
            border-radius: 4px;
            font-family: Arial, sans-serif;
            font-size: 13px;
        }
        .btn-split {
            background: #4caf50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
        }
        .btn-split:hover {
            background: #45a049;
        }
        .bulk-actions {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            border: 2px solid #4caf50;
        }
        .bulk-actions-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2e7d32;
        }
        .bulk-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn-bulk {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }
        .btn-select-missed {
            background: #ff9800;
            color: white;
        }
        .btn-select-missed:hover {
            background: #f57c00;
        }
        .btn-select-all {
            background: #2196f3;
            color: white;
        }
        .btn-select-all:hover {
            background: #1976d2;
        }
        .btn-deselect-all {
            background: #9e9e9e;
            color: white;
        }
        .btn-deselect-all:hover {
            background: #757575;
        }
        .btn-extract-all {
            background: #4caf50;
            color: white;
        }
        .btn-extract-all:hover {
            background: #45a049;
        }
        .pdf-checkbox {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        .pdf-card.selected {
            border: 3px solid #4caf50;
            background: #f1f8f4;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Verification Review</h1>
        <div class="stats">
            <div class="stat">
                <strong>Total Flagged:</strong> <span id="total-count">""" + str(len(flagged)) + """</span>
            </div>
            <div class="stat">
                <strong>Reviewed:</strong> <span id="reviewed-count">0</span>
            </div>
            <div class="stat">
                <strong>Correct:</strong> <span id="correct-count">0</span>
            </div>
            <div class="stat">
                <strong>Incorrect:</strong> <span id="incorrect-count">0</span>
            </div>
        </div>
        <div class="progress">
            <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
        </div>
    </div>
    
    <div class="bulk-actions">
        <div class="bulk-actions-title">🔀 Bulk Split Operations</div>
        <p style="font-size: 13px; color: #555; margin-bottom: 10px;">
            Select PDFs that need splitting, then extract song info for all of them at once.
        </p>
        <div class="bulk-buttons">
            <button class="btn-bulk btn-select-missed" onclick="selectMissedSplits()">
                ✓ Select All "Missed Split" Cases
            </button>
            <button class="btn-bulk btn-select-all" onclick="selectAll()">
                ✓ Select All PDFs
            </button>
            <button class="btn-bulk btn-deselect-all" onclick="deselectAll()">
                ✗ Deselect All
            </button>
            <button class="btn-bulk btn-extract-all" onclick="extractAllSelected()">
                📋 Extract Song Info for Selected
            </button>
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #666;">
            <strong>Selected:</strong> <span id="selected-count">0</span> PDFs
        </div>
    </div>
    
    <div id="pdf-list">
"""
    
    for idx, result in enumerate(flagged):
        html += f"""
        <div class="pdf-card" id="pdf-{idx}" data-reviewed="false">
            <div class="pdf-header">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" class="pdf-checkbox" id="checkbox-{idx}" onchange="toggleSelection({idx})">
                    <div>
                        <div class="pdf-title">{result['pdf_name']}</div>
                        <div class="pdf-path">{result['pdf_path']}</div>
                    </div>
                </div>
                <div>
                    <span id="status-{idx}"></span>
                    <button class="btn-clear" onclick="clearReview({idx})" style="display: none;" id="clear-{idx}">
                        Clear Review
                    </button>
                </div>
            </div>
            
            <div class="issues">
                <strong>Detected Issues:</strong>
"""
        for issue in result['issues']:
            html += f'                <div class="issue-item">• {issue}</div>\n'
        
        html += """            </div>
            
            <div class="pages-grid">
"""
        
        for page in result['page_analyses']:
            flagged_class = "flagged" if page['has_issue'] else ""
            flag_badge = "⚠️ FLAGGED" if page['has_issue'] else "✓ OK"
            
            html += f"""
                <div class="page-card {flagged_class}">
                    <div class="page-header">
                        <span>Page {page['page_num']}</span>
                        <span>{flag_badge}</span>
                    </div>
                    <img src="file:///{page['image_path']}" class="page-image" alt="Page {page['page_num']}">
                    <div class="bedrock-response">
                        <strong>Claude says:</strong> {page['bedrock_response']}
                    </div>
                </div>
"""
        
        html += f"""
            </div>
            
            <div class="review-buttons">
                <button class="btn btn-correct" onclick="markReview({idx}, 'correct')">
                    ✓ Detection is CORRECT (Real Issue)
                </button>
                <button class="btn btn-incorrect" onclick="markReview({idx}, 'incorrect')">
                    ✗ Detection is WRONG (False Positive)
                </button>
                <button class="btn btn-skip" onclick="markReview({idx}, 'skip')">
                    ⊘ Skip / Unsure
                </button>
            </div>
            
            <div class="feedback-section" id="feedback-{idx}" style="display: none;">
                <div class="feedback-title">Why is this a false positive? (Select all that apply)</div>
                <div class="feedback-options">
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'song-starts-midpage')">
                        Song starts mid-page (acceptable)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'guitar-tabs')">
                        Guitar tabs above music (normal)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'text-tabs')">
                        Text-only guitar tabs (no staff)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'extra-content')">
                        Extra content at end (photos/text)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'section-marker')">
                        Section marker (not new song)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'tempo-change')">
                        Tempo/key change (same song)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'title-midpage')">
                        Title mid-page (previous song ends)
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'continuation')">
                        Just continuation of song
                    </button>
                    <button class="feedback-btn" onclick="toggleFeedback({idx}, 'other')">
                        Other (explain below)
                    </button>
                </div>
                <textarea class="notes-input" id="notes-{idx}" placeholder="Additional notes or explanation..."></textarea>
            </div>
            
            <div class="feedback-section" id="correct-feedback-{idx}" style="display: none;">
                <div class="feedback-title">What type of error is this? (Select one)</div>
                <div class="feedback-options">
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'starts-mid-song-correct')">
                        ⚠️ Starts mid-song (SAME song, wrong start point)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'wrong-song-entirely')">
                        ❌ Wrong song entirely (DIFFERENT song)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'missed-split')">
                        🔀 Missed split (multiple songs in one PDF)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'extra-pages')">
                        📄 Extra pages (song continues into next song)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'multi-song-page')">
                        📑 Multiple songs on same page (need duplicate PDFs)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'starts-midpage-missing-prior')">
                        ⚡ Starts mid-page (prior song likely incomplete)
                    </button>
                    <button class="feedback-btn" onclick="toggleCorrectType({idx}, 'lyrics-only')">
                        📝 Lyrics on trailing page (acceptable - ignore)
                    </button>
                </div>
                <textarea class="notes-input" id="correct-notes-{idx}" placeholder="Additional details about the error..."></textarea>
            </div>
            
            <div class="split-section" id="split-{idx}" style="display: none;">
                <div class="split-title">🔀 Manual Split Tool</div>
                <p style="font-size: 13px; color: #555; margin-bottom: 10px;">
                    Click "Extract from Detection" to use the songs Claude identified when it flagged the split.
                </p>
                <button class="btn-split" onclick="extractFromDetection({idx})" id="extract-{idx}">
                    📋 Extract from Detection
                </button>
                <div id="split-songs-{idx}">
                    <div class="split-song-entry">
                        <input type="text" class="split-input" placeholder="Song 1 title" id="split-{idx}-song1-title">
                        <input type="text" class="split-input" placeholder="Pages (e.g., 1-3)" id="split-{idx}-song1-pages">
                    </div>
                    <div class="split-song-entry">
                        <input type="text" class="split-input" placeholder="Song 2 title" id="split-{idx}-song2-title">
                        <input type="text" class="split-input" placeholder="Pages (e.g., 4-7)" id="split-{idx}-song2-pages">
                    </div>
                </div>
                <button class="btn-split" onclick="addSplitSong({idx})">+ Add Another Song</button>
                <button class="btn-split" onclick="saveSplit({idx})">💾 Save Split Instructions</button>
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <script>
        // Initialize variables first
        let reviews = {};
        let feedbackData = {};
        let correctTypeData = {};
        let splitInstructions = {};
        let splitSongCounts = {};
        let selectedPdfs = new Set();
        
        // Define all functions BEFORE loading the large data
        window.toggleSelection = function(idx) {
            const checkbox = document.getElementById(`checkbox-${idx}`);
            const card = document.getElementById(`pdf-${idx}`);
            
            if (checkbox.checked) {
                selectedPdfs.add(idx);
                card.classList.add('selected');
            } else {
                selectedPdfs.delete(idx);
                card.classList.remove('selected');
            }
            
            updateSelectedCount();
        }
        
        window.updateSelectedCount = function() {
            document.getElementById('selected-count').textContent = selectedPdfs.size;
        }
        
        window.selectMissedSplits = function() {
            console.log('correctTypeData:', correctTypeData);
            // Select only PDFs marked with 'missed-split' error type
            let foundCount = 0;
            for (let i = 0; i < """ + str(len(flagged)) + """; i++) {
                const correctType = correctTypeData[i];
                console.log(`PDF ${i}:`, correctType);
                if (correctType && correctType.type === 'missed-split') {
                    foundCount++;
                    const checkbox = document.getElementById(`checkbox-${i}`);
                    if (checkbox) {
                        checkbox.checked = true;
                        selectedPdfs.add(i);
                        document.getElementById(`pdf-${i}`).classList.add('selected');
                    }
                }
            }
            console.log(`Found ${foundCount} missed-split PDFs`);
            updateSelectedCount();
            alert(`Selected ${selectedPdfs.size} PDFs marked as "Missed Split"`);
        }
        
        window.selectAll = function() {
            for (let i = 0; i < """ + str(len(flagged)) + """; i++) {
                const checkbox = document.getElementById(`checkbox-${i}`);
                if (checkbox) {
                    checkbox.checked = true;
                    selectedPdfs.add(i);
                    document.getElementById(`pdf-${i}`).classList.add('selected');
                }
            }
            updateSelectedCount();
        }
        
        window.deselectAll = function() {
            selectedPdfs.forEach(idx => {
                const checkbox = document.getElementById(`checkbox-${idx}`);
                if (checkbox) {
                    checkbox.checked = false;
                    document.getElementById(`pdf-${idx}`).classList.remove('selected');
                }
            });
            selectedPdfs.clear();
            updateSelectedCount();
        }
        
        // Embed page analyses data for extraction
        const allPageAnalyses = """ + json.dumps([[{
            'page_num': p['page_num'],
            'bedrock_response': p['bedrock_response'],
            'has_issue': p['has_issue']
        } for p in r['page_analyses']] for r in flagged]) + """;
        
        window.markReview = function(idx, status) {
            reviews[idx] = status;
            
            // Update UI
            const card = document.getElementById('pdf-' + idx);
            const statusDiv = document.getElementById('status-' + idx);
            const clearBtn = document.getElementById('clear-' + idx);
            const feedbackSection = document.getElementById('feedback-' + idx);
            const correctFeedbackSection = document.getElementById('correct-feedback-' + idx);
            const splitSection = document.getElementById('split-' + idx);
            
            card.classList.add('reviewed');
            card.dataset.reviewed = 'true';
            clearBtn.style.display = 'inline-block';
            
            if (status === 'correct') {
                statusDiv.innerHTML = '<span class="review-status status-correct">CORRECT</span>';
                feedbackSection.style.display = 'none';
                correctFeedbackSection.style.display = 'block';
                splitSection.style.display = 'none';
            } else if (status === 'incorrect') {
                statusDiv.innerHTML = '<span class="review-status status-incorrect">FALSE POSITIVE</span>';
                feedbackSection.style.display = 'block';
                correctFeedbackSection.style.display = 'none';
                splitSection.style.display = 'none';
            } else {
                statusDiv.innerHTML = '<span class="review-status status-skip">SKIPPED</span>';
                feedbackSection.style.display = 'none';
                correctFeedbackSection.style.display = 'none';
                splitSection.style.display = 'none';
            }
            
            // Update stats
            updateStats();
            
            // Save to localStorage
            saveData();
            
            // DON'T auto-scroll - let user stay on current item
        }
        
        window.clearReview = function(idx) {
            // Clear review status
            delete reviews[idx];
            delete feedbackData[idx];
            delete correctTypeData[idx];
            delete splitInstructions[idx];
            
            // Reset UI
            const card = document.getElementById('pdf-' + idx);
            const statusDiv = document.getElementById('status-' + idx);
            const clearBtn = document.getElementById('clear-' + idx);
            const feedbackSection = document.getElementById('feedback-' + idx);
            const correctFeedbackSection = document.getElementById('correct-feedback-' + idx);
            const splitSection = document.getElementById('split-' + idx);
            
            card.classList.remove('reviewed');
            card.dataset.reviewed = 'false';
            statusDiv.innerHTML = '';
            clearBtn.style.display = 'none';
            feedbackSection.style.display = 'none';
            correctFeedbackSection.style.display = 'none';
            splitSection.style.display = 'none';
            
            // Clear all selections
            feedbackSection.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));
            correctFeedbackSection.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));
            
            // Clear notes
            const notesInput = document.getElementById(`notes-${idx}`);
            if (notesInput) notesInput.value = '';
            const correctNotesInput = document.getElementById(`correct-notes-${idx}`);
            if (correctNotesInput) correctNotesInput.value = '';
            
            updateStats();
            saveData();
        }
        
        window.toggleFeedback = function(idx, reason) {
            if (!feedbackData[idx]) {
                feedbackData[idx] = { reasons: [], notes: '' };
            }
            
            const btn = event.target;
            const reasons = feedbackData[idx].reasons;
            
            if (reasons.includes(reason)) {
                reasons.splice(reasons.indexOf(reason), 1);
                btn.classList.remove('selected');
            } else {
                reasons.push(reason);
                btn.classList.add('selected');
            }
            
            saveData();
        }
        
        window.toggleCorrectType = function(idx, errorType) {
            if (!correctTypeData[idx]) {
                correctTypeData[idx] = { type: '', notes: '' };
            }
            
            // Clear all buttons in this section
            const section = document.getElementById('correct-feedback-' + idx);
            section.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));
            
            // Select this button
            event.target.classList.add('selected');
            correctTypeData[idx].type = errorType;
            
            // Show split section if missed-split or multi-song-page
            const splitSection = document.getElementById('split-' + idx);
            if (errorType === 'missed-split' || errorType === 'multi-song-page') {
                splitSection.style.display = 'block';
            } else {
                splitSection.style.display = 'none';
            }
            
            saveData();
        }
        
        window.extractFromDetection = function(idx) {
            // Use the pre-embedded page analyses data
            const pages = allPageAnalyses[idx];
            const songs = [];
            
            // Find first song from page 1
            const firstResponse = pages[0].bedrock_response;
            // Claude says things like: 'titled "Please Please Me"' or 'shows "Song Name"'
            const firstMatch = firstResponse.match(/"([^"]+)"/);
            if (firstMatch) {
                songs.push({
                    title: firstMatch[1],
                    startPage: 1,
                    endPage: null  // Will be set when we find next song
                });
            }
            
            // Find pages where Claude detected new songs (has_issue = true)
            pages.forEach(page => {
                if (page.has_issue) {
                    // Close previous song
                    if (songs.length > 0 && songs[songs.length - 1].endPage === null) {
                        songs[songs.length - 1].endPage = page.page_num - 1;
                    }
                    
                    // Extract new song title from Claude's response
                    // Claude says: "YES - This page shows the clear beginning of \"One After 909\""
                    const match = page.bedrock_response.match(/"([^"]+)"/);
                    if (match) {
                        songs.push({
                            title: match[1],
                            startPage: page.page_num,
                            endPage: null
                        });
                    }
                }
            });
            
            // Close last song
            if (songs.length > 0 && songs[songs.length - 1].endPage === null) {
                songs[songs.length - 1].endPage = pages[pages.length - 1].page_num;
            }
            
            if (songs.length === 0) {
                alert('No songs detected. Please enter manually.');
                return;
            }
            
            // Populate form
            const container = document.getElementById(`split-songs-${idx}`);
            container.innerHTML = '';
            
            songs.forEach((song, i) => {
                const pageRange = song.startPage === song.endPage ? 
                    `${song.startPage}` : 
                    `${song.startPage}-${song.endPage}`;
                    
                const entry = document.createElement('div');
                entry.className = 'split-song-entry';
                entry.innerHTML = `
                    <input type="text" class="split-input" value="${song.title}" id="split-${idx}-song${i+1}-title">
                    <input type="text" class="split-input" value="${pageRange}" id="split-${idx}-song${i+1}-pages">
                `;
                container.appendChild(entry);
            });
            
            splitSongCounts[idx] = songs.length;
            alert(`✓ Extracted ${songs.length} song(s)!`);
        }
        
        window.addSplitSong = function(idx) {
            if (!splitSongCounts[idx]) {
                splitSongCounts[idx] = 2;
            }
            splitSongCounts[idx]++;
            
            const container = document.getElementById(`split-songs-${idx}`);
            const newEntry = document.createElement('div');
            newEntry.className = 'split-song-entry';
            newEntry.innerHTML = `
                <input type="text" class="split-input" placeholder="Song ${splitSongCounts[idx]} title" id="split-${idx}-song${splitSongCounts[idx]}-title">
                <input type="text" class="split-input" placeholder="Pages (e.g., 7-9)" id="split-${idx}-song${splitSongCounts[idx]}-pages">
            `;
            container.appendChild(newEntry);
        }
        
        window.saveSplit = function(idx) {
            const songCount = splitSongCounts[idx] || 2;
            const songs = [];
            
            for (let i = 1; i <= songCount; i++) {
                const titleInput = document.getElementById(`split-${idx}-song${i}-title`);
                const pagesInput = document.getElementById(`split-${idx}-song${i}-pages`);
                
                if (titleInput && pagesInput && titleInput.value && pagesInput.value) {
                    songs.push({
                        title: titleInput.value,
                        pages: pagesInput.value
                    });
                }
            }
            
            if (songs.length > 0) {
                splitInstructions[idx] = songs;
                saveData();
                alert(`✓ Split instructions saved for ${songs.length} songs`);
            } else {
                alert('Please fill in at least one song title and page range');
            }
        }
        
        // Bulk operations functions
        window.toggleSelection = function(idx) {
            const checkbox = document.getElementById(`checkbox-${idx}`);
            const card = document.getElementById(`pdf-${idx}`);
            
            if (checkbox.checked) {
                selectedPdfs.add(idx);
                card.classList.add('selected');
            } else {
                selectedPdfs.delete(idx);
                card.classList.remove('selected');
            }
            
            updateSelectedCount();
        }
        
        window.extractAllSelected = function() {
            if (selectedPdfs.size === 0) {
                alert('No PDFs selected. Please select PDFs first.');
                return;
            }
            
            let successCount = 0;
            let failCount = 0;
            const results = [];
            
            selectedPdfs.forEach(idx => {
                try {
                    // Use the pre-embedded page analyses data
                    const pages = allPageAnalyses[idx];
                    const songs = [];
                    
                    // Find first song from page 1
                    const firstResponse = pages[0].bedrock_response;
                    const firstMatch = firstResponse.match(/"([^"]+)"/);
                    if (firstMatch) {
                        songs.push({
                            title: firstMatch[1],
                            startPage: 1,
                            endPage: null
                        });
                    }
                    
                    // Find pages where Claude detected new songs (has_issue = true)
                    pages.forEach(page => {
                        if (page.has_issue) {
                            // Close previous song
                            if (songs.length > 0 && songs[songs.length - 1].endPage === null) {
                                songs[songs.length - 1].endPage = page.page_num - 1;
                            }
                            
                            // Extract new song title from Claude's response
                            const match = page.bedrock_response.match(/"([^"]+)"/);
                            if (match) {
                                songs.push({
                                    title: match[1],
                                    startPage: page.page_num,
                                    endPage: null
                                });
                            }
                        }
                    });
                    
                    // Close last song
                    if (songs.length > 0 && songs[songs.length - 1].endPage === null) {
                        songs[songs.length - 1].endPage = pages[pages.length - 1].page_num;
                    }
                    
                    if (songs.length === 0) {
                        failCount++;
                        results.push(`PDF ${idx}: No songs detected`);
                    } else {
                        // Populate form
                        const container = document.getElementById(`split-songs-${idx}`);
                        container.innerHTML = '';
                        
                        songs.forEach((song, i) => {
                            const pageRange = song.startPage === song.endPage ? 
                                `${song.startPage}` : 
                                `${song.startPage}-${song.endPage}`;
                                
                            const entry = document.createElement('div');
                            entry.className = 'split-song-entry';
                            entry.innerHTML = `
                                <input type="text" class="split-input" value="${song.title}" id="split-${idx}-song${i+1}-title">
                                <input type="text" class="split-input" value="${pageRange}" id="split-${idx}-song${i+1}-pages">
                            `;
                            container.appendChild(entry);
                        });
                        
                        splitSongCounts[idx] = songs.length;
                        successCount++;
                        results.push(`PDF ${idx}: Extracted ${songs.length} song(s)`);
                    }
                } catch (error) {
                    failCount++;
                    results.push(`PDF ${idx}: Error - ${error.message}`);
                }
            });
            
            // Show results
            const message = `Extraction Complete!\\n\\n` +
                `✓ Success: ${successCount}\\n` +
                `✗ Failed: ${failCount}\\n\\n` +
                `Details:\\n${results.join('\\n')}`;
            
            alert(message);
        }
        
        window.saveData = function() {
            // Save notes
            document.querySelectorAll('.notes-input').forEach(textarea => {
                const match = textarea.id.match(/notes-(\d+)/);
                if (match) {
                    const idx = parseInt(match[1]);
                    if (feedbackData[idx]) {
                        feedbackData[idx].notes = textarea.value;
                    }
                }
                
                const correctMatch = textarea.id.match(/correct-notes-(\d+)/);
                if (correctMatch) {
                    const idx = parseInt(correctMatch[1]);
                    if (correctTypeData[idx]) {
                        correctTypeData[idx].notes = textarea.value;
                    }
                }
            });
            
            localStorage.setItem('pdf-reviews', JSON.stringify(reviews));
            localStorage.setItem('pdf-feedback', JSON.stringify(feedbackData));
            localStorage.setItem('pdf-correct-types', JSON.stringify(correctTypeData));
            localStorage.setItem('pdf-split-instructions', JSON.stringify(splitInstructions));
            localStorage.setItem('pdf-selected', JSON.stringify(Array.from(selectedPdfs)));
        }
        
        window.updateStats = function() {
            const total = """ + str(len(flagged)) + """;
            const reviewed = Object.keys(reviews).length;
            const correct = Object.values(reviews).filter(v => v === 'correct').length;
            const incorrect = Object.values(reviews).filter(v => v === 'incorrect').length;
            
            document.getElementById('reviewed-count').textContent = reviewed;
            document.getElementById('correct-count').textContent = correct;
            document.getElementById('incorrect-count').textContent = incorrect;
            
            const progress = (reviewed / total) * 100;
            document.getElementById('progress-bar').style.width = progress + '%';
        }
        
        window.scrollToNext = function(currentIdx) {
            for (let i = currentIdx + 1; i < """ + str(len(flagged)) + """; i++) {
                const card = document.getElementById('pdf-' + i);
                if (card.dataset.reviewed === 'false') {
                    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return;
                }
            }
        }
        
        // Load saved reviews
        const savedReviews = localStorage.getItem('pdf-reviews');
        const savedFeedback = localStorage.getItem('pdf-feedback');
        const savedCorrectTypes = localStorage.getItem('pdf-correct-types');
        const savedSplitInstructions = localStorage.getItem('pdf-split-instructions');
        const savedSelected = localStorage.getItem('pdf-selected');
        
        if (savedReviews) {
            reviews = JSON.parse(savedReviews);
            for (const [idx, status] of Object.entries(reviews)) {
                const idxNum = parseInt(idx);
                reviews[idxNum] = status;
                
                // Restore UI without calling markReview (to avoid side effects)
                const card = document.getElementById('pdf-' + idxNum);
                const statusDiv = document.getElementById('status-' + idxNum);
                const clearBtn = document.getElementById('clear-' + idxNum);
                
                if (card) {
                    card.classList.add('reviewed');
                    card.dataset.reviewed = 'true';
                    if (clearBtn) clearBtn.style.display = 'inline-block';
                    
                    if (status === 'correct') {
                        statusDiv.innerHTML = '<span class="review-status status-correct">CORRECT</span>';
                    } else if (status === 'incorrect') {
                        statusDiv.innerHTML = '<span class="review-status status-incorrect">FALSE POSITIVE</span>';
                    } else {
                        statusDiv.innerHTML = '<span class="review-status status-skip">SKIPPED</span>';
                    }
                }
            }
            updateStats();
        }
        
        if (savedFeedback) {
            feedbackData = JSON.parse(savedFeedback);
            
            // Restore feedback selections
            for (const [idx, data] of Object.entries(feedbackData)) {
                if (data.reasons) {
                    data.reasons.forEach(reason => {
                        const btns = document.querySelectorAll(`#feedback-${idx} .feedback-btn`);
                        btns.forEach(btn => {
                            if (btn.onclick.toString().includes(`'${reason}'`)) {
                                btn.classList.add('selected');
                            }
                        });
                    });
                }
                if (data.notes) {
                    const notesInput = document.getElementById(`notes-${idx}`);
                    if (notesInput) {
                        notesInput.value = data.notes;
                    }
                }
            }
        }
        
        if (savedCorrectTypes) {
            correctTypeData = JSON.parse(savedCorrectTypes);
            
            // Restore correct type selections
            for (const [idx, data] of Object.entries(correctTypeData)) {
                if (data.type) {
                    const btns = document.querySelectorAll(`#correct-feedback-${idx} .feedback-btn`);
                    btns.forEach(btn => {
                        if (btn.onclick.toString().includes(`'${data.type}'`)) {
                            btn.classList.add('selected');
                        }
                    });
                }
                if (data.notes) {
                    const notesInput = document.getElementById(`correct-notes-${idx}`);
                    if (notesInput) {
                        notesInput.value = data.notes;
                    }
                }
            }
        }
        
        if (savedSplitInstructions) {
            splitInstructions = JSON.parse(savedSplitInstructions);
        }
        
        if (savedSelected) {
            const selectedArray = JSON.parse(savedSelected);
            selectedArray.forEach(idx => {
                selectedPdfs.add(idx);
                const checkbox = document.getElementById(`checkbox-${idx}`);
                if (checkbox) {
                    checkbox.checked = true;
                    document.getElementById(`pdf-${idx}`).classList.add('selected');
                }
            });
            updateSelectedCount();
        }
        
        // Auto-save notes on input
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('notes-input') || e.target.classList.contains('split-input')) {
                saveData();
            }
        });
        
        // Export function
        window.exportReviews = function() {
            const exportData = {
                summary: {
                    total: """ + str(len(flagged)) + """,
                    reviewed: Object.keys(reviews).length,
                    correct: Object.values(reviews).filter(v => v === 'correct').length,
                    incorrect: Object.values(reviews).filter(v => v === 'incorrect').length,
                    skipped: Object.values(reviews).filter(v => v === 'skip').length,
                    false_positive_rate: Object.keys(reviews).length > 0 ? 
                        (Object.values(reviews).filter(v => v === 'incorrect').length / Object.keys(reviews).length * 100).toFixed(1) + '%' : '0.0%'
                },
                reviews: reviews,
                feedback: feedbackData,
                correctTypes: correctTypeData,
                splitInstructions: splitInstructions,
                timestamp: new Date().toISOString()
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'review_feedback_' + new Date().toISOString().split('T')[0] + '.json';
            a.click();
        }
        
        // Clear all reviews
        window.clearAllReviews = function() {
            if (!confirm('Are you sure you want to clear ALL reviews? This cannot be undone.')) {
                return;
            }
            
            reviews = {};
            feedbackData = {};
            correctTypeData = {};
            splitInstructions = {};
            splitSongCounts = {};
            
            // Reset all UI
            for (let i = 0; i < """ + str(len(flagged)) + """; i++) {
                const card = document.getElementById('pdf-' + i);
                const statusDiv = document.getElementById('status-' + i);
                const clearBtn = document.getElementById('clear-' + i);
                const feedbackSection = document.getElementById('feedback-' + i);
                const correctFeedbackSection = document.getElementById('correct-feedback-' + i);
                const splitSection = document.getElementById('split-' + i);
                
                if (card) {
                    card.classList.remove('reviewed');
                    card.dataset.reviewed = 'false';
                    statusDiv.innerHTML = '';
                    if (clearBtn) clearBtn.style.display = 'none';
                    if (feedbackSection) feedbackSection.style.display = 'none';
                    if (correctFeedbackSection) correctFeedbackSection.style.display = 'none';
                    if (splitSection) splitSection.style.display = 'none';
                    
                    // Clear all selections
                    if (feedbackSection) feedbackSection.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));
                    if (correctFeedbackSection) correctFeedbackSection.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));
                    
                    // Clear notes
                    const notesInput = document.getElementById(`notes-${i}`);
                    if (notesInput) notesInput.value = '';
                    const correctNotesInput = document.getElementById(`correct-notes-${i}`);
                    if (correctNotesInput) correctNotesInput.value = '';
                }
            }
            
            updateStats();
            saveData();
            alert('All reviews cleared');
        }
        
        // Add export and clear all buttons
        window.addEventListener('load', () => {
            const header = document.querySelector('.header');
            
            const buttonContainer = document.createElement('div');
            buttonContainer.style.marginTop = '10px';
            buttonContainer.style.display = 'flex';
            buttonContainer.style.gap = '10px';
            
            const exportBtn = document.createElement('button');
            exportBtn.textContent = '💾 Export Reviews';
            exportBtn.className = 'btn btn-correct';
            exportBtn.onclick = exportReviews;
            
            const clearAllBtn = document.createElement('button');
            clearAllBtn.textContent = '🗑️ Clear All Reviews';
            clearAllBtn.className = 'btn btn-incorrect';
            clearAllBtn.onclick = clearAllReviews;
            
            buttonContainer.appendChild(exportBtn);
            buttonContainer.appendChild(clearAllBtn);
            header.appendChild(buttonContainer);
        });
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Review page generated: {output_file}")
    print(f"  Flagged PDFs: {len(flagged)}")
    print(f"\nOpen in browser: file:///{output_file.absolute()}")


if __name__ == "__main__":
    # Check for filtered results first
    filtered_file = Path("verification_results/batch1_results_filtered.json")
    results_file = filtered_file if filtered_file.exists() else Path("verification_results/bedrock_results.json")
    output_file = Path("verification_results/review_page.html")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found")
        print("Run verification first: py run_verification_with_output.py <pdf_list>")
    else:
        generate_html(results_file, output_file)
