import http.server
import socketserver
import json
import sqlite3
import os
from datetime import datetime

PORT = 8000
DB_FILE = 'memo.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class MemoHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def do_GET(self):
        if self.path == '/api/notes':
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM notes ORDER BY created_at DESC')
            notes = [dict(row) for row in c.fetchall()]
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(notes).encode())
        else:
            # Serve normal files (index.html)
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/notes':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            title = data.get('title', '')
            content = data.get('content', '')
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            now_str = datetime.now().isoformat()
            c.execute('INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)', 
                      (title, content, now_str, now_str))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'id': new_id, 'title': title, 'content': content, 'created_at': now_str}).encode())
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path.startswith('/api/notes/'):
            note_id = self.path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            title = data.get('title', '')
            content = data.get('content', '')
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            now_str = datetime.now().isoformat()
            c.execute('UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?', 
                      (title, content, now_str, note_id))
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/api/notes/'):
            note_id = self.path.split('/')[-1]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'deleted'}).encode())
        else:
            self.send_error(404)

if __name__ == '__main__':
    init_db()
    
    # Ensure current directory is served correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MemoHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
