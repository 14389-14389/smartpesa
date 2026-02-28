import http.server
import socketserver
import webbrowser
import os

PORT = 3000
DIRECTORY = "frontend"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

print("=" * 60)
print("🚀 SmartPesa PWA Frontend Server")
print("=" * 60)
print(f"\n📱 Frontend URL: http://localhost:{PORT}")
print(f"🔧 Backend URL: http://localhost:8000")
print(f"\n💡 Make sure:")
print(f"   • Backend is running on port 8000")
print(f"   • You're logged in with test@example.com")
print(f"\n✨ Opening browser automatically...\n")

# Open browser
webbrowser.open(f'http://localhost:{PORT}')

# Start server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🎯 Frontend server running on http://localhost:{PORT}")
    print("   Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
