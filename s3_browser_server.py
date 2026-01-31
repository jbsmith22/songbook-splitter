"""
Local server for S3 browser with delete and compare functionality.
"""
import boto3
import json
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import webbrowser
import threading

class S3BrowserHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the HTML page."""
        if self.path == '/' or self.path == '/index.html':
            try:
                with open('s3_bucket_browser_interactive.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            except Exception as e:
                self.send_error(500, f"Error loading page: {str(e)}")
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        """Handle delete and compare requests."""
        if self.path == '/delete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            path = data.get('path')
            is_folder = data.get('isFolder', False)
            
            try:
                s3 = boto3.client('s3')
                bucket = 'jsmith-output'
                
                if is_folder:
                    # Delete all objects with this prefix
                    deleted_count = self.delete_folder(s3, bucket, path)
                    message = f"Deleted folder '{path}' ({deleted_count} objects)"
                else:
                    # Delete single file
                    s3.delete_object(Bucket=bucket, Key=path)
                    message = f"Deleted file '{path}'"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': True, 'message': message}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"✅ {message}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"❌ Error: {str(e)}")
        
        elif self.path == '/compare':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            folder1 = data.get('folder1')
            folder2 = data.get('folder2')
            
            try:
                print(f"\n🔍 Comparing folders:")
                print(f"   Folder 1: {folder1}")
                print(f"   Folder 2: {folder2}")
                
                result = self.compare_folders(folder1, folder2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
                print(f"✅ Comparison complete:")
                print(f"   Identical: {result['stats']['identical']}")
                print(f"   Different: {result['stats']['different']}")
                print(f"   Only in folder 1: {result['stats']['only_in_1']}")
                print(f"   Only in folder 2: {result['stats']['only_in_2']}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"❌ Error: {str(e)}")
        
        elif self.path == '/move':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            source_path = data.get('sourcePath')
            dest_path = data.get('destPath')
            delete_source = data.get('deleteSource', True)
            
            try:
                s3 = boto3.client('s3')
                bucket = 'jsmith-output'
                
                # Copy the file
                copy_source = {'Bucket': bucket, 'Key': source_path}
                s3.copy_object(CopySource=copy_source, Bucket=bucket, Key=dest_path)
                
                # Delete source if move (not copy)
                if delete_source:
                    s3.delete_object(Bucket=bucket, Key=source_path)
                    action = "Moved"
                else:
                    action = "Copied"
                
                message = f"{action} '{source_path}' to '{dest_path}'"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': True, 'message': message}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"✅ {message}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"❌ Error: {str(e)}")
        
        elif self.path == '/batch-move':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            operations = data.get('operations', [])
            
            try:
                s3 = boto3.client('s3')
                bucket = 'jsmith-output'
                
                results = []
                success_count = 0
                error_count = 0
                
                print(f"\n📦 Batch operation: {len(operations)} files")
                
                for op in operations:
                    source_path = op['sourcePath']
                    dest_path = op['destPath']
                    delete_source = op.get('deleteSource', True)
                    
                    try:
                        # Copy the file
                        copy_source = {'Bucket': bucket, 'Key': source_path}
                        s3.copy_object(CopySource=copy_source, Bucket=bucket, Key=dest_path)
                        
                        # Delete source if move (not copy)
                        if delete_source:
                            s3.delete_object(Bucket=bucket, Key=source_path)
                            action = "Moved"
                        else:
                            action = "Copied"
                        
                        results.append({
                            'success': True,
                            'file': source_path,
                            'message': f"{action} successfully"
                        })
                        success_count += 1
                        print(f"  ✅ {action}: {source_path}")
                        
                    except Exception as e:
                        results.append({
                            'success': False,
                            'file': source_path,
                            'message': str(e)
                        })
                        error_count += 1
                        print(f"  ❌ Error: {source_path} - {str(e)}")
                
                message = f"Batch complete: {success_count} succeeded, {error_count} failed"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'success': True,
                    'message': message,
                    'results': results,
                    'stats': {
                        'total': len(operations),
                        'success': success_count,
                        'failed': error_count
                    }
                }
                self.wfile.write(json.dumps(response).encode())
                
                print(f"\n✅ {message}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"❌ Error: {str(e)}")
        
        else:
            self.send_error(404, "Endpoint not found")
    
    def delete_folder(self, s3, bucket, prefix):
        """Delete all objects with the given prefix."""
        # Ensure prefix ends with /
        if not prefix.endswith('/'):
            prefix += '/'
        
        deleted_count = 0
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            objects = [{'Key': obj['Key']} for obj in page['Contents']]
            if objects:
                s3.delete_objects(Bucket=bucket, Delete={'Objects': objects})
                deleted_count += len(objects)
        
        return deleted_count
    
    def compare_folders(self, folder1, folder2):
        """Compare two folders byte-by-byte using MD5 hashes."""
        s3 = boto3.client('s3')
        bucket = 'jsmith-output'
        
        # Ensure folders end with /
        if not folder1.endswith('/'):
            folder1 += '/'
        if not folder2.endswith('/'):
            folder2 += '/'
        
        # Get files from both folders
        files1 = self.get_folder_files(s3, bucket, folder1)
        files2 = self.get_folder_files(s3, bucket, folder2)
        
        # Compare files
        identical = []
        different = []
        only_in_1 = []
        only_in_2 = []
        
        # Get relative paths
        files1_dict = {self.get_relative_path(f['Key'], folder1): f for f in files1}
        files2_dict = {self.get_relative_path(f['Key'], folder2): f for f in files2}
        
        all_files = set(files1_dict.keys()) | set(files2_dict.keys())
        
        for rel_path in sorted(all_files):
            if rel_path in files1_dict and rel_path in files2_dict:
                # File exists in both - compare
                file1 = files1_dict[rel_path]
                file2 = files2_dict[rel_path]
                
                # Compare using ETag (MD5 hash for non-multipart uploads)
                if file1['ETag'] == file2['ETag'] and file1['Size'] == file2['Size']:
                    identical.append({
                        'path': rel_path,
                        'size': file1['Size'],
                        'etag': file1['ETag']
                    })
                else:
                    different.append({
                        'path': rel_path,
                        'size1': file1['Size'],
                        'size2': file2['Size'],
                        'etag1': file1['ETag'],
                        'etag2': file2['ETag']
                    })
            elif rel_path in files1_dict:
                only_in_1.append({
                    'path': rel_path,
                    'size': files1_dict[rel_path]['Size']
                })
            else:
                only_in_2.append({
                    'path': rel_path,
                    'size': files2_dict[rel_path]['Size']
                })
        
        return {
            'success': True,
            'folder1': folder1,
            'folder2': folder2,
            'identical': identical,
            'different': different,
            'only_in_1': only_in_1,
            'only_in_2': only_in_2,
            'stats': {
                'identical': len(identical),
                'different': len(different),
                'only_in_1': len(only_in_1),
                'only_in_2': len(only_in_2),
                'total_files_1': len(files1),
                'total_files_2': len(files2)
            }
        }
    
    def get_folder_files(self, s3, bucket, prefix):
        """Get all files in a folder."""
        files = []
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                # Skip the folder itself
                if obj['Key'] != prefix:
                    files.append(obj)
        
        return files
    
    def get_relative_path(self, full_path, prefix):
        """Get relative path by removing prefix."""
        if full_path.startswith(prefix):
            return full_path[len(prefix):]
        return full_path
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

def start_server(port=8080):
    """Start the HTTP server."""
    server = HTTPServer(('localhost', port), S3BrowserHandler)
    print(f"🌐 Server started at http://localhost:{port}")
    print(f"📦 Bucket: jsmith-output")
    print(f"⚠️  WARNING: Delete operations are permanent!")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    # Open browser after a short delay
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        server.shutdown()

if __name__ == '__main__':
    start_server()
