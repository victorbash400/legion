# legion_adk/main.py
from dotenv import load_dotenv
load_dotenv()  # Add this line at the very top
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from typing import List, Dict, Any
import uuid
import asyncio
import json
from datetime import datetime
from api.streaming import stream_tasks, stream_operations, stream_comms, stream_manager_instance


# Import models
from api.models import Message, Chat

# Import ADK components - UPDATED FOR ADK SYSTEM
from agents.legion_system import LegionADKSystem
from services.state_manager import state_manager # Import the global state manager
from api.streaming import stream_tasks, stream_operations, stream_comms

app = FastAPI(title="Legion ADK Integration Server", version="1.0.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# In-memory storage for chats (unchanged interface) 
chats_storage: dict = {}

# Initialize Legion ADK system - UPDATED TO USE ADK SYSTEM
legion_system = LegionADKSystem(state_manager=state_manager)

# Connect WebSocket connections to state_manager
state_manager.set_websocket_connections(active_connections)

# WebSocket endpoint
state_manager.set_stream_manager(stream_manager_instance)

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    await websocket.accept()
    active_connections[chat_id] = websocket
    print(f"WebSocket connected for chat: {chat_id}")
    
    try:
        while True:
            # Keep connection alive (receive any messages from frontend)
            data = await websocket.receive_text()
            print(f"Received WebSocket message from {chat_id}: {data}")
    except WebSocketDisconnect:
        if chat_id in active_connections:
            del active_connections[chat_id]
        print(f"WebSocket disconnected for chat: {chat_id}")
    except Exception as e:
        print(f"WebSocket error for chat {chat_id}: {e}")
        if chat_id in active_connections:
            del active_connections[chat_id]

# Chat endpoints - USED BY FRONTEND (UNCHANGED interface) 
@app.get("/api/chats", response_model=List[Chat])
async def get_all_chats():
    """Get all chats."""
    return list(chats_storage.values())

@app.post("/api/chats", response_model=Chat)
async def create_new_chat(chat: Chat):
    """Create a new chat. """
    if chat.chatId in chats_storage:
        raise HTTPException(status_code=400, detail="Chat ID already exists")

    chat_data = chat.dict()
    chats_storage[chat.chatId] = chat_data

    # Initialize research data for this chat through the state manager
    state_manager._initialize_chat_state(chat.chatId) # Directly call private method for initial state

    return chat_data

@app.get("/api/chats/{chat_id}", response_model=Chat)
async def get_chat_by_id(chat_id: str):
    """Get a specific chat by ID."""
    if chat_id not in chats_storage:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chats_storage[chat_id]

@app.post("/api/chats/{chat_id}/messages", response_model=Message)
async def save_message_and_get_ai_response(chat_id: str, user_message: Message):
    """
    Save a user message to a chat and route it through the enhanced ADK Consul conversation flow.
    """
    if chat_id not in chats_storage:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Generate message ID and timestamp for user message if not provided 
    if not user_message.id:
        user_message.id = str(uuid.uuid4())
    if not user_message.timestamp:
        user_message.timestamp = datetime.now().replace(microsecond=0).isoformat() + "Z"

    # Add user message to chat storage (UNCHANGED) 
    chats_storage[chat_id]["messages"].append(user_message.dict())

    # Route message through enhanced ADK Consul conversation flow (async task)
    asyncio.create_task(
        handle_adk_consul_conversation(chat_id, user_message.content)
    )

    # Return immediate acknowledgment (WebSocket will handle the real response)
    ai_message = Message(
        id=str(uuid.uuid4()),
        content="Processing your message through ADK agent system...",
        role='assistant',
        timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z"
    )

    return ai_message

async def handle_adk_consul_conversation(chat_id: str, user_message: str):
    """
    Handle the enhanced ADK conversational Consul flow and manage ADK workflow execution.
    Updated for ADK orchestration and agent-to-agent communication with rich context handoff.
    ENHANCED: Now properly handles question-driven workflow detection and routing.
    """
    try:
        # Route message to enhanced ADK Consul for conversational handling
        consul_response = await legion_system.consul.handle_user_message(chat_id, user_message)
        
        # The enhanced ADK Consul handles its own state updates to the frontend
        # through state_manager.update_frontend_state() calls, so we don't need to
        # manually add messages to chat storage here for most cases.
        
        # However, we still add the final response to chat storage for persistence
        if consul_response.get("message"):
            # Add Consul's response to chat messages for persistence
            consul_msg = Message(
                id=str(uuid.uuid4()),
                content=consul_response["message"],
                role='assistant',
                timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z"
            )
            chats_storage[chat_id]["messages"].append(consul_msg.dict())
        
        # Handle different response statuses from enhanced ADK system
        status = consul_response.get("status")
        
        if status == "mission_approved" and consul_response.get("ready_to_execute"):
            # User approved the plan, now execute the ADK workflow with rich context
            print(f"MAIN: ADK mission approved for chat {chat_id}, starting workflow execution...")
            
            # Add system message about ADK workflow start
            mission_start_msg = Message(
                id=str(uuid.uuid4()),
                content="SYSTEM: ADK Workflow execution beginning. Enhanced agents will now collaborate conversationally...",
                role='assistant',
                timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z"
            )
            chats_storage[chat_id]["messages"].append(mission_start_msg.dict())
            
            # Update state manager that ADK workflow is starting
            await state_manager.update_frontend_state(
                chat_id,
                {
                    "event": "mission_initiated",  # Frontend listens for this
                    "message": "ADK agents have begun conversational collaboration",
                    "mission_status": "ACTIVE",
                    "mission_type": "research"
                }
            )
            
            # Create rich mission context from CONSUL's work (ENHANCED FOR QUESTION-DRIVEN)
            mission_context = await extract_rich_mission_context(chat_id, user_message, consul_response)
            
            # Enhanced logging for question-driven workflow
            workflow_type = "question-driven" if mission_context.get("use_question_driven") else "traditional"
            question_count = len(mission_context.get("research_questions", []))
            
            print(f"MAIN: Starting {workflow_type} ADK workflow with rich mission context:")
            print(f"  Research Focus: {mission_context.get('research_focus', 'not specified')}")
            print(f"  Mission Title: {mission_context.get('mission_plan', {}).get('mission_title', 'not specified')}")
            print(f"  Objectives Count: {len(mission_context.get('mission_plan', {}).get('objectives', []))}")
            if workflow_type == "question-driven":
                print(f"  Research Questions: {question_count} questions generated")
                for i, q in enumerate(mission_context.get("research_questions", [])[:3], 1):
                    print(f"    Q{i}: {q.get('question', 'Unknown question')[:80]}...")
            
            # Set research questions in state manager for tracking
            if mission_context.get("research_questions"):
                await state_manager.set_research_questions(chat_id, mission_context["research_questions"])
            
            # Start the actual ADK workflow execution with enhanced context
            await legion_system.start_mission_with_context(chat_id, mission_context)
            
        elif status in ["continuing_conversation", "needs_clarification", "greeting_handled"]:
            # ADK Consul is handling the conversation flow - no additional action needed
            # The enhanced Consul already sent its response to the frontend via state_manager
            print(f"MAIN: ADK Consul continuing conversation in chat {chat_id} (status: {status})")
            
        elif status == "mission_error":
            # Handle ADK workflow errors
            error_msg = Message(
                id=str(uuid.uuid4()),
                content=f"SYSTEM: ADK Workflow error - {consul_response.get('message', 'Unknown error')}",
                role='assistant',
                timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z"
            )
            chats_storage[chat_id]["messages"].append(error_msg.dict())
            
            await state_manager.update_frontend_state(
                chat_id,
                {
                    "event": "adk_workflow_error",
                    "message": consul_response.get('message', 'Unknown error occurred in ADK workflow')
                }
            )
            
    except Exception as e:
        print(f"MAIN: Error in ADK Consul conversation: {str(e)}")
        # Add error message to chat
        error_msg = Message(
            id=str(uuid.uuid4()),
            content=f"ADK CONSUL: I encountered an error processing your request. Please try again.",
            role='assistant',
            timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z"
        )
        chats_storage[chat_id]["messages"].append(error_msg.dict())
        
        await state_manager.update_frontend_state(
            chat_id,
            {
                "event": "adk_workflow_error",
                "message": "Error in ADK conversation processing"
            }
        )

async def extract_rich_mission_context(chat_id: str, user_message: str, consul_response: Dict) -> Dict[str, Any]:
    """
    Extract rich mission context from CONSUL's conversation state and response.
    ENHANCED: Now properly extracts research questions and sets question-driven workflow flags.
    """
    mission_context = {
        "chat_id": chat_id,
        "original_user_message": user_message,
        "mission_plan": consul_response.get("mission_plan", {}),
        "research_focus": "research topic",  # Default fallback
        "conversation_history": [],
        # NEW: Question-driven workflow support
        "research_questions": consul_response.get("research_questions", []),
        "use_question_driven": False  # Will be set based on questions
    }
    
    # Determine if we should use question-driven workflow
    research_questions = mission_context["research_questions"]
    if research_questions and len(research_questions) > 0:
        mission_context["use_question_driven"] = True
        print(f"MAIN: Question-driven workflow detected with {len(research_questions)} questions")
        
        # Log the questions for debugging
        for i, q in enumerate(research_questions[:3], 1):  # Show first 3 questions
            question_text = q.get("question", "Unknown question") if isinstance(q, dict) else str(q)
            print(f"  Q{i}: {question_text[:80]}...")
    else:
        print("MAIN: Traditional workflow - no research questions found")
    
    # Get CONSUL's conversation state for rich context
    if hasattr(legion_system.consul, 'conversations') and chat_id in legion_system.consul.conversations:
        conv = legion_system.consul.conversations[chat_id]
        
        # Store conversation history for context
        mission_context["conversation_history"] = conv.get("messages", [])
        
        # Enhanced research questions extraction from conversation state
        if not mission_context["research_questions"] and conv.get("research_questions"):
            mission_context["research_questions"] = conv["research_questions"]
            mission_context["use_question_driven"] = len(mission_context["research_questions"]) > 0
            print(f"MAIN: Found research questions in CONSUL conversation state: {len(mission_context['research_questions'])} questions")
        
        # Priority 1: Use stored research_context if available
        if conv.get("research_context"):
            mission_context["research_focus"] = conv["research_context"]
            print(f"MAIN: Using CONSUL's research_context: '{mission_context['research_focus']}'")
        
        # Priority 2: Extract from mission plan objectives (BEST SOURCE)
        elif mission_context["mission_plan"] and mission_context["mission_plan"].get("objectives"):
            objectives = mission_context["mission_plan"]["objectives"]
            if objectives and len(objectives) > 0:
                # Use the first objective as it contains the most specific context
                mission_context["research_focus"] = objectives[0]
                print(f"MAIN: Using mission objective as research focus: '{mission_context['research_focus']}'")
        
        # Priority 3: Clean up mission title if that's all we have
        elif mission_context["mission_plan"] and mission_context["mission_plan"].get("mission_title"):
            title = mission_context["mission_plan"]["mission_title"]
            if ":" in title:
                # Extract everything after the colon and clean it up
                topic = title.split(":", 1)[1].strip()
                # Remove generic suffixes that don't help agents
                suffixes_to_remove = [
                    "A Comprehensive Analysis", "Analysis", 
                    "A General Overview", "Overview", "Research", "Study"
                ]
                for suffix in suffixes_to_remove:
                    if topic.endswith(suffix):
                        topic = topic[:-len(suffix)].strip()
                
                if topic and len(topic) > 3:
                    mission_context["research_focus"] = topic
                    print(f"MAIN: Using cleaned mission title: '{mission_context['research_focus']}'")
        
        # Priority 4: Find original research question in conversation messages
        if mission_context["research_focus"] == "research topic":
            for msg in conv.get("messages", []):
                if msg.get("role") == "user":
                    msg_content = msg.get("content", "").strip()
                    
                    # Skip approval/greeting messages
                    skip_patterns = [
                        "hi", "hello", "hey", "yes", "ok", "sounds good", 
                        "proceed", "go", "start", "sounds right", "looks good",
                        "that works", "perfect", "great", "let's do it"
                    ]
                    
                    is_skip = any(pattern in msg_content.lower() for pattern in skip_patterns)
                    
                    # Look for substantial research topics
                    if len(msg_content) > 10 and not is_skip:
                        mission_context["research_focus"] = msg_content
                        print(f"MAIN: Found original research topic in messages: '{mission_context['research_focus']}'")
                        break
    
    # Add extracted research topic to mission plan parameters for agents
    if mission_context["mission_plan"]:
        mission_context["mission_plan"]["extracted_research_focus"] = mission_context["research_focus"]
    
    # Enhanced workflow context logging
    workflow_summary = {
        "workflow_type": "question-driven" if mission_context["use_question_driven"] else "traditional",
        "research_focus": mission_context["research_focus"],
        "question_count": len(mission_context["research_questions"]),
        "has_mission_plan": bool(mission_context["mission_plan"])
    }
    print(f"MAIN: Mission context extracted: {workflow_summary}")
    
    return mission_context

# Enhanced endpoint to get ADK conversation status
@app.get("/api/chats/{chat_id}/consul-status")
async def get_consul_status(chat_id: str):
    """Get the current ADK Consul conversation status for a chat."""
    
    # Get enhanced ADK Consul's internal conversation state
    consul_conversations = getattr(legion_system.consul, 'conversations', {})
    consul_state = consul_conversations.get(chat_id, {})
    
    return {
        "chat_id": chat_id,
        "system_type": "ADK_Enhanced",
        "has_conversation": chat_id in consul_conversations,
        "message_count": len(consul_state.get("messages", [])),
        "has_mission_plan": consul_state.get("mission_plan") is not None,
        "has_research_questions": consul_state.get("research_questions") is not None,
        "question_count": len(consul_state.get("research_questions", [])),
        "plan_ready": consul_state.get("plan_ready", False),
        "research_context": consul_state.get("research_context"),
        "mission_plan": consul_state.get("mission_plan"),
        "research_questions": consul_state.get("research_questions", [])[:3],  # Show first 3 questions
        "workflow_type": "question-driven" if consul_state.get("research_questions") else "traditional",
        "adk_features": {
            "orchestration": True,
            "a2a_communication": True,
            "conversational_agents": True,
            "question_driven_research": True
        }
    }

# NEW ADK-SPECIFIC ENDPOINTS

@app.get("/api/adk/capabilities")
async def get_adk_capabilities():
    """Get ADK system capabilities and agent information."""
    return legion_system.get_adk_capabilities()

@app.get("/api/adk/agent-conversations/{chat_id}")
async def get_agent_conversations(chat_id: str):
    """Get agent-to-agent conversation history."""
    try:
        return {
            "chat_id": chat_id,
            "conversations": {
                "consul_centurion": await legion_system.get_agent_conversation_history(chat_id, "consul", "centurion"),
                "centurion_augur": await legion_system.get_agent_conversation_history(chat_id, "centurion", "augur"),
                "augur_scribe": await legion_system.get_agent_conversation_history(chat_id, "augur", "scribe")
            },
            "system_type": "ADK_Enhanced"
        }
    except Exception as e:
        print(f"Error getting agent conversations for chat {chat_id}: {e}")
        return {
            "chat_id": chat_id,
            "conversations": {},
            "error": str(e)
        }

@app.post("/api/adk/demo-conversation/{chat_id}")
async def demo_agent_conversation(chat_id: str):
    """Demonstrate ADK agent conversation capabilities."""
    try:
        return await legion_system.demonstrate_agent_conversation(chat_id)
    except Exception as e:
        print(f"Error in ADK demo for chat {chat_id}: {e}")
        return {
            "status": "demo_failed",
            "error": str(e),
            "chat_id": chat_id
        }

@app.get("/api/adk/workflow-status/{chat_id}")
async def get_adk_workflow_status(chat_id: str):
    """Get comprehensive ADK workflow and agent status."""
    try:
        return await legion_system.get_mission_status(chat_id)
    except Exception as e:
        print(f"Error getting ADK workflow status for chat {chat_id}: {e}")
        return {
            "chat_id": chat_id,
            "system_type": "ADK_Enhanced",
            "status": "error",
            "error": str(e)
        }

# NEW: Question-driven research specific endpoints
@app.get("/api/research/{chat_id}/questions")
async def get_research_questions(chat_id: str):
    """Get research questions and their progress for question-driven workflow."""
    try:
        questions_data = await state_manager.get_research_questions(chat_id)
        return {
            "chat_id": chat_id,
            "workflow_type": questions_data.get("workflow_type", "traditional"),
            "questions": questions_data.get("questions", []),
            "answered_questions": questions_data.get("answered_questions", []),
            "progress": questions_data.get("progress", {}),
            "total_questions": questions_data.get("total_questions", 0),
            "completed_questions": questions_data.get("completed_questions", 0),
            "overall_progress": int((questions_data.get("completed_questions", 0) / max(questions_data.get("total_questions", 1), 1)) * 100)
        }
    except Exception as e:
        print(f"Error getting research questions for chat {chat_id}: {e}")
        return {
            "chat_id": chat_id,
            "workflow_type": "traditional",
            "questions": [],
            "error": str(e)
        }

@app.get("/api/research/{chat_id}/workflow-status")
async def get_question_workflow_status(chat_id: str):
    """Get comprehensive question-driven workflow status."""
    try:
        return await state_manager.get_question_workflow_status(chat_id)
    except Exception as e:
        print(f"Error getting question workflow status for chat {chat_id}: {e}")
        return {
            "chat_id": chat_id,
            "workflow_type": "traditional",
            "error": str(e)
        }

# Research streaming endpoints - USED BY FRONTEND (Enhanced for ADK) 
@app.get("/api/research/{chat_id}/tasks/stream")
async def get_stream_tasks(chat_id: str):
    return await stream_tasks(chat_id)

@app.get("/api/research/{chat_id}/operations/stream")
async def get_stream_operations(chat_id: str):
    return await stream_operations(chat_id)

@app.get("/api/research/{chat_id}/comms/stream")
async def get_stream_comms(chat_id: str):
    return await stream_comms(chat_id)

@app.get("/api/research/{chat_id}/deliverables")
async def get_deliverables(chat_id: str):
    """Get current deliverables for a chat."""
    try:
        deliverables = await state_manager.get_deliverables(chat_id)
        # Ensure we return in the expected format
        return {
            "deliverables": deliverables,
            "total": len(deliverables),
            "chat_id": chat_id,
            "system_type": "ADK_Enhanced"
        }
    except Exception as e:
        print(f"Error getting deliverables for chat {chat_id}: {e}")
        return {
            "deliverables": [],
            "total": 0,
            "chat_id": chat_id,
            "error": str(e)
        }

@app.get("/api/research/{chat_id}/deliverables/{deliverable_id}")
async def get_deliverable_by_id(chat_id: str, deliverable_id: str):
    """Get a specific deliverable by ID."""
    try:
        deliverables = await state_manager.get_deliverables(chat_id)
        
        # Find deliverable by title
        for deliverable in deliverables:
            if deliverable.get("title") == deliverable_id:
                return deliverable
        
        raise HTTPException(status_code=404, detail="Deliverable not found")
    except Exception as e:
        print(f"Error getting deliverable {deliverable_id} for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/{chat_id}/deliverables/{deliverable_id}/download")
async def download_deliverable(chat_id: str, deliverable_id: str):
    """Download a deliverable as a file."""
    try:
        deliverables = await state_manager.get_deliverables(chat_id)
        
        # Find deliverable by title
        deliverable = None
        for d in deliverables:
            if d.get("title") == deliverable_id:
                deliverable = d
                break
        
        if not deliverable:
            raise HTTPException(status_code=404, detail="Deliverable not found")
        
        # Prepare file content
        content = deliverable.get("content", "")
        filename = f"{deliverable_id}.md"
        
        # Create response with proper headers for file download
        return Response(
            content=content.encode('utf-8'),
            media_type='text/markdown',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/markdown; charset=utf-8"
            }
        )
        
    except Exception as e:
        print(f"Error downloading deliverable {deliverable_id} for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Optional non-streaming research endpoints (for direct retrieval, enhanced for ADK)
@app.get("/api/research/{chat_id}/tasks")
async def get_tasks(chat_id: str):
    """Get current tasks for a chat (non-streaming)."""
    return await state_manager.get_agent_tasks(chat_id)

@app.get("/api/research/{chat_id}/operations")
async def get_operations(chat_id: str):
    """Get current operations for a chat (non-streaming)."""
    return await state_manager.get_agent_operations(chat_id)

@app.get("/api/research/{chat_id}/comms")
async def get_comms(chat_id: str):
    """Get current communications for a chat (non-streaming)."""
    return await state_manager.get_agent_comms(chat_id)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Legion ADK System with conversational agent collaboration...")
    print("✅ ADK Orchestration: Enabled")
    print("✅ A2A Communication: Enabled") 
    print("✅ Conversational Agents: Enabled")
    print("✅ Question-Driven Research: Enabled")
    print("✅ Real-time Streaming: Enabled")
    uvicorn.run(app, host="0.0.0.0", port=3001)