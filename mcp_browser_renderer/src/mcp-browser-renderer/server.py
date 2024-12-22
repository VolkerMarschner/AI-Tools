import asyncio
import http.server
import os
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Create a simple HTTP server to serve our content
class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

class BrowserServer:
    def __init__(self, port: int = 8000):
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        # Use user's home directory for temp files
        self.temp_dir = Path.home() / ".mcp-browser-renderer"
        self.temp_dir.mkdir(exist_ok=True)
        
    def start_server(self):
        """Start the HTTP server in a separate thread"""
        os.chdir(self.temp_dir)
        handler = SimpleHTTPRequestHandler
        while True:
            try:
                self.server = socketserver.TCPServer(("", self.port), handler)
                break
            except OSError:
                # If port is in use, try the next one
                self.port += 1
        
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            
    def create_and_open(self, content: str, filename: str = "index.html"):
        """Create an HTML file and open it in the browser"""
        file_path = self.temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        webbrowser.open(f"http://localhost:{self.port}/{filename}")

# Initialize the MCP server
app = Server("browser-renderer")
browser_server = BrowserServer()

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools for the MCP server"""
    return [
        types.Tool(
            name="b-render",
            description="Render HTML/JavaScript content in a local browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "HTML/JavaScript content to render"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the HTML file (default: index.html)"
                    }
                },
                "required": ["content"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool execution requests"""
    if name == "b-render":
        content = arguments["content"]
        filename = arguments.get("filename", "index.html")
        
        # Create and open the HTML file
        browser_server.create_and_open(content, filename)
        
        return [
            types.TextContent(
                type="text",
                text=f"Content rendered in browser at http://localhost:{browser_server.port}/{filename}"
            )
        ]
    
    raise ValueError(f"Unknown tool: {name}")

async def run_server():
    """Run the MCP server"""
    # Start the browser server
    browser_server.start_server()
    
    try:
        # Run the MCP server
        async with stdio_server() as streams:
            await app.run(
                streams[0],
                streams[1],
                InitializationOptions(
                    server_name="browser-renderer",
                    server_version="0.1.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        # Clean up
        browser_server.stop_server()

def main():
    """Entry point for the package"""
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
