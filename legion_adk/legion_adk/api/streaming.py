# legion_adk/api/streaming.py

import json
import asyncio
from fastapi import HTTPException
from sse_starlette.sse import EventSourceResponse
from services.state_manager import state_manager

# Event-driven approach: Store client generators to push updates immediately
_active_streams = {
    "tasks": {},
    "operations": {},
    "comms": {}
}

class StreamManager:
    """Manages real-time streams for different data types"""
    
    @staticmethod
    async def notify_tasks_update(chat_id: str, tasks_data):
        """Notify all task stream clients for a specific chat"""
        if chat_id in _active_streams["tasks"]:
            for client_queue in _active_streams["tasks"][chat_id]:
                try:
                    await client_queue.put(tasks_data)
                except:
                    pass  # Client disconnected
    
    @staticmethod
    async def notify_operations_update(chat_id: str, operations_data):
        """Notify all operations stream clients for a specific chat"""
        if chat_id in _active_streams["operations"]:
            for client_queue in _active_streams["operations"][chat_id]:
                try:
                    await client_queue.put(operations_data)
                except:
                    pass  # Client disconnected
    
    @staticmethod
    async def notify_comms_update(chat_id: str, comms_data):
        """Notify all comms stream clients for a specific chat"""
        if chat_id in _active_streams["comms"]:
            for client_queue in _active_streams["comms"][chat_id]:
                try:
                    await client_queue.put(comms_data)
                except:
                    pass  # Client disconnected

# Make stream manager available to state_manager
stream_manager_instance = StreamManager()

async def stream_tasks(chat_id: str):
    """Stream tasks for a specific chat - event-driven updates"""
    client_queue = asyncio.Queue()
    
    # Register this client
    if chat_id not in _active_streams["tasks"]:
        _active_streams["tasks"][chat_id] = []
    _active_streams["tasks"][chat_id].append(client_queue)
    
    async def generate():
        try:
            # Send initial data
            initial_tasks = await state_manager.get_agent_tasks(chat_id)
            yield {
                "event": "tasks",
                "data": json.dumps(initial_tasks)
            }
            
            # Wait for real-time updates
            while True:
                try:
                    # Wait for new data with timeout to handle client disconnections
                    tasks_data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield {
                        "event": "tasks",
                        "data": json.dumps(tasks_data)
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"status": "connected"})
                    }
                except asyncio.CancelledError:
                    break
                    
        except Exception as e:
            print(f"Error in tasks stream for chat {chat_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            # Cleanup: remove this client
            if chat_id in _active_streams["tasks"]:
                try:
                    _active_streams["tasks"][chat_id].remove(client_queue)
                    if not _active_streams["tasks"][chat_id]:
                        del _active_streams["tasks"][chat_id]
                except ValueError:
                    pass
            print(f"Client disconnected from tasks stream for chat {chat_id}")
    
    return EventSourceResponse(generate())

async def stream_operations(chat_id: str):
    """Stream operations for a specific chat - event-driven updates"""
    client_queue = asyncio.Queue()
    
    # Register this client
    if chat_id not in _active_streams["operations"]:
        _active_streams["operations"][chat_id] = []
    _active_streams["operations"][chat_id].append(client_queue)
    
    async def generate():
        try:
            # Send initial data
            initial_operations = await state_manager.get_agent_operations(chat_id)
            yield {
                "event": "operations",
                "data": json.dumps(initial_operations)
            }
            
            # Wait for real-time updates
            while True:
                try:
                    operations_data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield {
                        "event": "operations",
                        "data": json.dumps(operations_data)
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"status": "connected"})
                    }
                except asyncio.CancelledError:
                    break
                    
        except Exception as e:
            print(f"Error in operations stream for chat {chat_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            # Cleanup
            if chat_id in _active_streams["operations"]:
                try:
                    _active_streams["operations"][chat_id].remove(client_queue)
                    if not _active_streams["operations"][chat_id]:
                        del _active_streams["operations"][chat_id]
                except ValueError:
                    pass
            print(f"Client disconnected from operations stream for chat {chat_id}")
    
    return EventSourceResponse(generate())

async def stream_comms(chat_id: str):
    """Stream agent communications for a specific chat - event-driven updates"""
    client_queue = asyncio.Queue()
    
    # Register this client
    if chat_id not in _active_streams["comms"]:
        _active_streams["comms"][chat_id] = []
    _active_streams["comms"][chat_id].append(client_queue)
    
    async def generate():
        try:
            # Send initial data
            initial_comms = await state_manager.get_agent_comms(chat_id)
            yield {
                "event": "comms",
                "data": json.dumps(initial_comms)
            }
            
            # Wait for real-time updates
            while True:
                try:
                    comms_data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield {
                        "event": "comms",
                        "data": json.dumps(comms_data)
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"status": "connected"})
                    }
                except asyncio.CancelledError:
                    break
                    
        except Exception as e:
            print(f"Error in comms stream for chat {chat_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            # Cleanup
            if chat_id in _active_streams["comms"]:
                try:
                    _active_streams["comms"][chat_id].remove(client_queue)
                    if not _active_streams["comms"][chat_id]:
                        del _active_streams["comms"][chat_id]
                except ValueError:
                    pass
            print(f"Client disconnected from comms stream for chat {chat_id}")
    
    return EventSourceResponse(generate())