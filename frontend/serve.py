#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🌐 Frontend server running at: http://localhost:{PORT}")
        print(f"📁 Serving from: {DIRECTORY}")
        print("📋 Instructions:")
        print("   1. Make sure backend is running: cd backend && python main.py")
        print("   2. Open browser to: http://localhost:3000")
        print("   3. Test streaming chat!")
        print(f"   4. Press Ctrl+C to stop")
        
        try:
            # Try to open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    main()