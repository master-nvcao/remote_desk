import tkinter as tk
import threading
import socketserver
import http.server
import logging
import os
import sys
import socket

# Set up logging to file for debugging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to get the correct path for index.html
def get_html_path():
    """Get the path to the index.html file, accounting for bundling by PyInstaller."""
    if getattr(sys, 'frozen', False):
        # If the app is bundled, use the temporary folder PyInstaller creates
        base_path = sys._MEIPASS
    else:
        # If running from the source code, use the current directory
        base_path = os.path.dirname(__file__)
    
    html_path = os.path.join(base_path, "index.html")
    logging.debug(f"HTML file path: {html_path}")
    return html_path

# HTTP Server
def start_http_server():
    """Start the HTTP server to serve the index.html page."""
    try:
        html_path = get_html_path()
        logging.debug(f"Serving index.html from: {html_path}")
        
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                """Override translate_path to return the correct path for index.html"""
                if path == "/index.html":
                    return html_path
                return super().translate_path(path)

        handler = CustomHandler
        with socketserver.TCPServer(("0.0.0.0", 8080), handler) as httpd:
            logging.debug("Starting HTTP server on port 8080")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Error starting server: {str(e)}")

# WebSocket Server (example, if needed)
def start_websocket_server():
    """WebSocket server for handling WebSocket connections."""
    try:
        import websockets
        import asyncio

        async def handle_connection(websocket, path):
            while True:
                message = await websocket.recv()
                print(f"Received message: {message}")

        start_server = websockets.serve(handle_connection, "0.0.0.0", 8765)
        asyncio.get_event_loop().run_until_complete(start_server)
        logging.info("WebSocket server started on port 8765")
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        logging.error(f"WebSocket server error: {str(e)}")

# Function to start both servers in separate threads
def start_servers():
    """Start both the HTTP and WebSocket servers in separate threads."""
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)

    http_thread.start()
    websocket_thread.start()

# Tkinter GUI Setup
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Server Control")
        self.geometry("400x300")

        # Label to show the IP address
        self.ip_label = tk.Label(self, text="IP Address: ", font=("Arial", 12))
        self.ip_label.pack(pady=20)

        # Button to start the server
        self.start_button = tk.Button(self, text="Start Server", command=self.start_servers, font=("Arial", 12))
        self.start_button.pack(pady=10)

        # Status label
        self.status_label = tk.Label(self, text="Server is stopped", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Call the function to update the IP address in the GUI
        self.update_ip_address()

    def update_ip_address(self):
        """Update the IP address on the GUI."""
        import socket
        ip_address = self.get_ip_address()
        self.ip_label.config(text=f"IP Address: {ip_address}")

        # Update the IP address every 1 second
        self.after(1000, self.update_ip_address)

    def get_ip_address(self):
        """Get the local IP address of the machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(('10.254.254.254', 1))  # Try to connect to a non-existent address
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address

    def start_servers(self):
        """Start the servers when the button is clicked."""
        self.start_button.config(state=tk.DISABLED)  # Disable the button after starting the server
        self.status_label.config(text="Server is running...")
        start_servers()  # Start both servers in separate threads

if __name__ == "__main__":
    app = App()
    app.mainloop()
