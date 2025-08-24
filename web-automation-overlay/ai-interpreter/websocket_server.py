"""
websocket_server.py - WebSocket server for browser-AI communication
"""

import asyncio
import websockets
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time browser communication"""

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def register_client(self, websocket):
        """Register new client connection"""
        self.clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id}")

        # Send welcome message
        await websocket.send(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))

    async def unregister_client(self, websocket):
        """Remove client connection"""
        self.clients.discard(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client disconnected: {client_id}")

    async def handle_message(self, websocket, message: str):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            logger.info(f"Received message type: {message_type}")

            if message_type == "EXECUTE_SEQUENCE":
                response = await self.handle_execute_sequence(data)
            elif message_type == "ANALYZE_PAGE":
                response = await self.handle_analyze_page(data)
            elif message_type == "GET_STATUS":
                response = await self.handle_get_status(data)
            elif message_type == "STOP_EXECUTION":
                response = await self.handle_stop_execution(data)
            else:
                response = {
                    "type": "ERROR",
                    "error": f"Unknown message type: {message_type}"
                }

            # Send response back to client
            await websocket.send(json.dumps(response))

        except json.JSONDecodeError as e:
            error_response = {
                "type": "ERROR",
                "error": f"Invalid JSON: {str(e)}"
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            logger.error(traceback.format_exc())
            error_response = {
                "type": "ERROR",
                "error": str(e)
            }
            await websocket.send(json.dumps(error_response))

    async def handle_execute_sequence(self, data: Dict[str, Any]):
        """Process action sequence execution request"""
        sequence = data.get("sequence")
        session_id = sequence.get("session_id")

        # Store session
        self.active_sessions[session_id] = {
            "sequence": sequence,
            "start_time": datetime.now().isoformat(),
            "status": "executing"
        }

        # Process and optimize sequence
        from action_protocol import ActionSequence
        seq = ActionSequence.from_json(json.dumps(sequence))
        optimized = seq.optimize_for_tokens()

        return {
            "type": "SEQUENCE_RESPONSE",
            "session_id": session_id,
            "status": "accepted",
            "optimized_tokens": len(optimized.split()),
            "original_tokens": len(json.dumps(sequence).split()),
            "token_reduction": f"{(1 - len(optimized.split()) / len(json.dumps(sequence).split())) * 100:.1f}%"
        }

    async def handle_analyze_page(self, data: Dict[str, Any]):
        """Analyze page structure request"""
        page_data = data.get("page_data", {})

        # Perform analysis (simplified)
        analysis = {
            "forms_count": len(page_data.get("forms", [])),
            "inputs_count": len(page_data.get("inputs", [])),
            "buttons_count": len(page_data.get("buttons", [])),
            "suggested_actions": []
        }

        # Generate suggested actions based on page structure
        if page_data.get("inputs"):
            for input_field in page_data["inputs"][:3]:  # First 3 inputs
                if input_field.get("type") == "text":
                    analysis["suggested_actions"].append({
                        "type": "type",
                        "target": input_field.get("id") or input_field.get("name"),
                        "description": f"Fill {input_field.get('label', 'text field')}"
                    })

        return {
            "type": "ANALYSIS_RESPONSE",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_get_status(self, data: Dict[str, Any]):
        """Get execution status"""
        session_id = data.get("session_id")
        session = self.active_sessions.get(session_id)

        if session:
            return {
                "type": "STATUS_RESPONSE",
                "session_id": session_id,
                "status": session["status"],
                "start_time": session["start_time"]
            }
        else:
            return {
                "type": "STATUS_RESPONSE",
                "session_id": session_id,
                "status": "not_found"
            }

    async def handle_stop_execution(self, data: Dict[str, Any]):
        """Stop execution request"""
        session_id = data.get("session_id")

        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "stopped"
            return {
                "type": "STOP_RESPONSE",
                "session_id": session_id,
                "status": "stopped"
            }
        else:
            return {
                "type": "STOP_RESPONSE",
                "session_id": session_id,
                "status": "not_found"
            }

    async def broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )

    async def client_handler(self, websocket, path):
        """Handle client connection lifecycle"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    async def start(self):
        """Start WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self.client_handler, self.host, self.port):
            logger.info(f"Server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

def main():
    """Main entry point"""
    server = WebSocketServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()
