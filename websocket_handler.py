# websocket_handler.py

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connected_clients = set()

async def progress_update(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            pass
    finally:
        connected_clients.remove(websocket)

async def notify_clients(message):
    if connected_clients:
        await asyncio.gather(*[client.send(message) for client in connected_clients])

def send_progress_update(node_name, status):
    message = json.dumps({"node": node_name, "status": status})
    asyncio.run(notify_clients(message))

def node_wrapper(node_func, node_name, state):
    try:
        send_progress_update(node_name, "in_progress")
        result = node_func(state)
        send_progress_update(node_name, "completed")
        return result
    except Exception as e:
        send_progress_update(node_name, "error")
        logger.error(f"Error in node {node_name}: {e}")
        raise e

def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(progress_update, "0.0.0.0", 6790)
    loop.run_until_complete(start_server)
    loop.run_forever()
