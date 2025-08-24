#!/bin/bash
# Start WebSocket server for Web Automation Overlay

echo "Starting Web Automation Overlay Server..."
cd ai-interpreter
pip install -r requirements.txt
python websocket_server.py
