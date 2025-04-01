import asyncio
import pyautogui
import websockets
import json
import socket
import http.server
import socketserver
import tkinter as tk
import threading
from pathlib import Path
import sys
import os

# Configuration
HTTP_PORT = 8080
WS_PORT = 8765
HTML_TEMP = "temp.html"
HTML_FILE = "index.html"


def get_html_path():
    """Get the path to the index.html file, accounting for bundling by PyInstaller."""
    if getattr(sys, 'frozen', False):
        # If the app is bundled, use the temporary folder PyInstaller creates
        base_path = sys._MEIPASS
    else:
        # If running from the source code, use the current directory
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, "index.html")


def get_local_ip():
    """Get the IP address of the active network interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # This doesn't actually connect to 8.8.8.8; it just figures out the IP needed to reach it
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = "127.0.0.1"  # Fallback to localhost if there's an issue
    return ip_address


async def handle_client(websocket):
    """Handle incoming WebSocket connections and control mouse/keyboard."""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")

                # Handle mouse actions
                if action == "left_click":
                    pyautogui.click()
                elif action == "right_click":
                    pyautogui.rightClick()

                # Handle keyboard actions
                elif action == "press_key":
                    key = data.get("key")
                    pyautogui.press(key)

                # New functionalities
                elif action == "fullscreen":
                    pyautogui.press("f")
                elif action == "exit_fullscreen":
                    pyautogui.press("esc")
                elif action == "minimize_all":
                    pyautogui.hotkey("win", "d")
                elif action == "play_pause":
                    pyautogui.press("playpause")
                elif action == "mute":
                    pyautogui.press("volumemute")
                elif action == "volume_up":
                    pyautogui.press("volumeup")
                elif action == "volume_down":
                    pyautogui.press("volumedown")
            except Exception as e:
                print(f"Error processing message: {message} | Exception: {e}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"WebSocket connection closed unexpectedly: {e}")
    except Exception as e:
        print(f"Unexpected error in WebSocket handler: {e}")


async def start_websocket_server():
    """Start the WebSocket server to handle remote commands."""
    try:
        async with websockets.serve(
            handle_client, "0.0.0.0", WS_PORT, ping_interval=20, ping_timeout=20
        ):
            print("WebSocket server is running and listening on port", WS_PORT)
            
            await asyncio.Future()  # Keep running indefinitely
    except Exception as e:
        print(f"Failed to start WebSocket server: {e}")
        


def start_http_server():
    """Start the HTTP server to serve the index.html page."""
    html_path = get_html_path()

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            """Override translate_path to return the correct path for index.html"""
            if path == "/index.html":
                return html_path
            return super().translate_path(path)

    handler = CustomHandler
    with socketserver.TCPServer(("0.0.0.0", HTTP_PORT), handler) as httpd:
        httpd.serve_forever()


def update_html_file(ip_address):
    html_temp = Path(HTML_TEMP)
    html_file = Path(HTML_FILE)
    if html_temp.exists():
        with open(html_temp, "r") as file:
            content = file.read()

        # Update WebSocket IP in the file
        new_content = content.replace(
            "ws://localhost:port", f"ws://{ip_address}:{WS_PORT}"
        )

        with open(html_file, "w") as file:
            file.write(new_content)


def run_gui(ip_address):
    """Run a Tkinter GUI to display the IP address and access link."""
    root = tk.Tk()
    root.geometry("700x150")
    root.title("Remote Control Server")

    link = f"http://{ip_address}:{HTTP_PORT}/index.html"

    if ip_address == "127.0.0.1":
        label_link = tk.Label(
            root,
            text="Not connected to any Network. Please connect to a network.",
            fg="red",
            cursor="hand2",
            font=("Helvetica", 18),
        )
        label_link.pack(pady=10, anchor="center")
    else:
        # Center the labels using pack with expand=True and anchor='center'
        label_ip = tk.Label(
            root, text=f"Computer IP Address: {ip_address}", font=("Helvetica", 18)
        )
        label_ip.pack(pady=10, anchor="center")

        label_link = tk.Label(
            root,
            text=f"Access from phone: {link}",
            fg="blue",
            cursor="hand2",
            font=("Helvetica", 14),
        )
        label_link.pack(pady=10, anchor="center")

        # Open link in browser on click
        def open_link(event):
            import webbrowser

            webbrowser.open(link)

        label_link.bind("<Button-1>", open_link)

    root.mainloop()

def main():
    # Get the local IP address
    ip_address = get_local_ip()

    # Update the HTML file with the current IP address
    update_html_file(ip_address)


    # Start the WebSocket server in the background
    threading.Thread(
        target=lambda: asyncio.run(start_websocket_server()), daemon=True
    ).start()

    # Start the HTTP server in the background
    threading.Thread(target=start_http_server, daemon=True).start()

    run_gui(ip_address)


if __name__ == "__main__":
    main()
