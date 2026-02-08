"""
Generate an interactive hierarchical browser for S3 bucket contents
"""
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def parse_s3_listing(listing_file):
    """Parse S3 listing file into hierarchical structure"""
    structure = defaultdict(lambda: defaultdict(list))
    total_size = 0
    file_count = 0

    with open(listing_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                # Parse: 2026-01-27 01:30:11    2084894 Artist/Album/Song.pdf
                parts = line.strip().split(maxsplit=3)
                if len(parts) < 4:
                    continue

                date_str = parts[0]
                time_str = parts[1]
                size = int(parts[2])
                path = parts[3]

                # Split path into components
                path_parts = path.split('/')
                if len(path_parts) < 3:
                    continue  # Skip non-standard paths

                artist = path_parts[0]
                album = path_parts[1]
                filename = '/'.join(path_parts[2:])  # Handle nested paths

                structure[artist][album].append({
                    'filename': filename,
                    'size': size,
                    'date': f"{date_str} {time_str}"
                })

                total_size += size
                file_count += 1

            except (ValueError, IndexError) as e:
                continue

    return dict(structure), total_size, file_count

def format_size(bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def generate_html(structure, total_size, file_count, output_file):
    """Generate interactive HTML page"""

    # Calculate statistics
    artist_count = len(structure)
    album_count = sum(len(albums) for albums in structure.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Songbook S3 Browser - {artist_count} Artists, {album_count} Albums, {file_count:,} Songs</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}

        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .search-box {{
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}

        .search-input {{
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }}

        .search-input:focus {{
            border-color: #667eea;
        }}

        .content {{
            padding: 30px;
            max-height: 800px;
            overflow-y: auto;
        }}

        .artist {{
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}

        .artist-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }}

        .artist-header:hover {{
            background: #5568d3;
        }}

        .artist-name {{
            font-size: 1.3em;
            font-weight: 600;
        }}

        .artist-stats {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .albums {{
            display: none;
            background: #f8f9fa;
            padding: 15px;
        }}

        .albums.show {{
            display: block;
        }}

        .album {{
            background: white;
            margin-bottom: 10px;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #e0e0e0;
        }}

        .album-header {{
            background: #764ba2;
            color: white;
            padding: 12px 18px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }}

        .album-header:hover {{
            background: #653a8a;
        }}

        .album-name {{
            font-size: 1.1em;
            font-weight: 500;
        }}

        .album-stats {{
            font-size: 0.85em;
            opacity: 0.9;
        }}

        .songs {{
            display: none;
            padding: 15px;
            background: #fafafa;
        }}

        .songs.show {{
            display: block;
        }}

        .song {{
            padding: 8px 12px;
            background: white;
            margin-bottom: 6px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 3px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .song:hover {{
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .song-name {{
            font-size: 0.95em;
            color: #333;
            flex: 1;
        }}

        .song-size {{
            font-size: 0.85em;
            color: #666;
            margin-left: 15px;
        }}

        .toggle-icon {{
            font-size: 1.2em;
            transition: transform 0.3s;
        }}

        .toggle-icon.open {{
            transform: rotate(90deg);
        }}

        .hidden {{
            display: none !important;
        }}

        .no-results {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.2em;
        }}

        ::-webkit-scrollbar {{
            width: 12px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 6px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Songbook Collection Browser</h1>
            <div class="stats">
                <div class="stat">
                    <span class="stat-value">{artist_count:,}</span>
                    <span class="stat-label">Artists</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{album_count:,}</span>
                    <span class="stat-label">Albums</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{file_count:,}</span>
                    <span class="stat-label">Songs</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{format_size(total_size)}</span>
                    <span class="stat-label">Total Size</span>
                </div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="Search for artists, albums, or songs...">
        </div>

        <div class="content" id="content">
"""

    # Sort artists alphabetically
    for artist in sorted(structure.keys()):
        albums = structure[artist]
        album_count_artist = len(albums)
        song_count_artist = sum(len(songs) for songs in albums.values())
        total_size_artist = sum(sum(song['size'] for song in songs) for songs in albums.values())

        html += f"""
            <div class="artist" data-artist="{artist.lower()}">
                <div class="artist-header" onclick="toggleArtist(this)">
                    <div class="artist-name">
                        <span class="toggle-icon">▶</span>
                        {artist}
                    </div>
                    <div class="artist-stats">
                        {album_count_artist} albums • {song_count_artist} songs • {format_size(total_size_artist)}
                    </div>
                </div>
                <div class="albums">
"""

        # Sort albums alphabetically
        for album in sorted(albums.keys()):
            songs = albums[album]
            song_count_album = len(songs)
            total_size_album = sum(song['size'] for song in songs)

            html += f"""
                    <div class="album" data-album="{album.lower()}">
                        <div class="album-header" onclick="toggleAlbum(this)">
                            <div class="album-name">
                                <span class="toggle-icon">▶</span>
                                {album}
                            </div>
                            <div class="album-stats">
                                {song_count_album} songs • {format_size(total_size_album)}
                            </div>
                        </div>
                        <div class="songs">
"""

            # Sort songs alphabetically
            for song in sorted(songs, key=lambda x: x['filename']):
                html += f"""
                            <div class="song" data-song="{song['filename'].lower()}">
                                <div class="song-name">{song['filename']}</div>
                                <div class="song-size">{format_size(song['size'])}</div>
                            </div>
"""

            html += """
                        </div>
                    </div>
"""

        html += """
                </div>
            </div>
"""

    html += """
        </div>
    </div>

    <script>
        function toggleArtist(element) {
            const albums = element.nextElementSibling;
            const icon = element.querySelector('.toggle-icon');
            albums.classList.toggle('show');
            icon.classList.toggle('open');
        }

        function toggleAlbum(element) {
            const songs = element.nextElementSibling;
            const icon = element.querySelector('.toggle-icon');
            songs.classList.toggle('show');
            icon.classList.toggle('open');
        }

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const content = document.getElementById('content');

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const artists = document.querySelectorAll('.artist');
            let visibleCount = 0;

            if (searchTerm === '') {
                // Show all, collapse all
                artists.forEach(artist => {
                    artist.classList.remove('hidden');
                    artist.querySelector('.albums').classList.remove('show');
                    artist.querySelector('.toggle-icon').classList.remove('open');

                    const albums = artist.querySelectorAll('.album');
                    albums.forEach(album => {
                        album.classList.remove('hidden');
                        album.querySelector('.songs').classList.remove('show');
                        album.querySelector('.toggle-icon').classList.remove('open');

                        const songs = album.querySelectorAll('.song');
                        songs.forEach(song => song.classList.remove('hidden'));
                    });
                });
                return;
            }

            artists.forEach(artist => {
                const artistName = artist.dataset.artist;
                const albums = artist.querySelectorAll('.album');
                let artistHasMatch = false;

                if (artistName.includes(searchTerm)) {
                    // Artist name matches - show everything
                    artist.classList.remove('hidden');
                    artist.querySelector('.albums').classList.add('show');
                    artist.querySelector('.toggle-icon').classList.add('open');

                    albums.forEach(album => {
                        album.classList.remove('hidden');
                        album.querySelector('.songs').classList.add('show');
                        album.querySelector('.toggle-icon').classList.add('open');

                        const songs = album.querySelectorAll('.song');
                        songs.forEach(song => song.classList.remove('hidden'));
                    });

                    artistHasMatch = true;
                    visibleCount++;
                } else {
                    // Check albums and songs
                    albums.forEach(album => {
                        const albumName = album.dataset.album;
                        const songs = album.querySelectorAll('.song');
                        let albumHasMatch = false;

                        if (albumName.includes(searchTerm)) {
                            // Album name matches - show all songs
                            album.classList.remove('hidden');
                            album.querySelector('.songs').classList.add('show');
                            album.querySelector('.toggle-icon').classList.add('open');

                            songs.forEach(song => song.classList.remove('hidden'));
                            albumHasMatch = true;
                            artistHasMatch = true;
                        } else {
                            // Check individual songs
                            let songMatches = 0;
                            songs.forEach(song => {
                                const songName = song.dataset.song;
                                if (songName.includes(searchTerm)) {
                                    song.classList.remove('hidden');
                                    songMatches++;
                                    albumHasMatch = true;
                                    artistHasMatch = true;
                                } else {
                                    song.classList.add('hidden');
                                }
                            });

                            if (albumHasMatch) {
                                album.classList.remove('hidden');
                                album.querySelector('.songs').classList.add('show');
                                album.querySelector('.toggle-icon').classList.add('open');
                            } else {
                                album.classList.add('hidden');
                            }
                        }
                    });

                    if (artistHasMatch) {
                        artist.classList.remove('hidden');
                        artist.querySelector('.albums').classList.add('show');
                        artist.querySelector('.toggle-icon').classList.add('open');
                        visibleCount++;
                    } else {
                        artist.classList.add('hidden');
                    }
                }
            });

            // Show "no results" message if needed
            if (visibleCount === 0) {
                let noResults = document.querySelector('.no-results');
                if (!noResults) {
                    noResults = document.createElement('div');
                    noResults.className = 'no-results';
                    noResults.textContent = 'No results found';
                    content.appendChild(noResults);
                }
            } else {
                const noResults = document.querySelector('.no-results');
                if (noResults) {
                    noResults.remove();
                }
            }
        });
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    listing_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/s3-output-listing.txt'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'web/s3-browser/songbook-browser.html'

    print(f"Parsing S3 listing from {listing_file}...")
    structure, total_size, file_count = parse_s3_listing(listing_file)

    print(f"Found {len(structure)} artists, {file_count:,} files, {format_size(total_size)}")

    print(f"Generating HTML to {output_file}...")
    generate_html(structure, total_size, file_count, output_file)

    print(f"✓ Done! Open {output_file} in your browser.")
