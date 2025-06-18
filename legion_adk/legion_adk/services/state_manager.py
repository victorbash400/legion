# legion_adk/services/state_manager.py - UPDATED VERSION WITH QUESTION TASK SUPPORT

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# In-memory storage for simplicity, will be replaced by Firestore
_research_storage: Dict[str, Dict[str, Any]] = {}

class StateManager:
    """
    Bridge between ADK agents and frontend expectations. 
    Manages the synchronization of ADK agent states with the frontend data structures.
    UPDATED: Enhanced with question-driven research support and question task integration
    """

    def __init__(self):
        self.active_connections = {}
        self.stream_manager = None

    def set_websocket_connections(self, connections_dict):
        """Set the WebSocket connections dictionary from main.py"""
        self.active_connections = connections_dict
        
    def set_stream_manager(self, stream_manager):
        """Set the stream manager for real-time notifications"""
        self.stream_manager = stream_manager

    def _initialize_chat_state(self, chat_id: str) -> None:
        """Initializes the in-memory state for a new chat if it doesn't exist."""
        if chat_id not in _research_storage:
            _research_storage[chat_id] = {
                "tasks": [
                    {"id": 1, "title": "Awaiting user request", "status": "pending", "type": "planning"}
                ],
                # COMMS = Agent-to-agent conversations (actual chat messages)
                "comms": [],
                
                # OPERATIONS = What agents are actively doing (workspace activities)  
                "operations": [],
                
                "deliverables": [],
                "mission_state": "PENDING",
                "adk_context": {},
                "consul_conversation": {
                    "stage": "initial",
                    "messages": [],
                    "plan": None
                },
                
                # NEW: Question-driven research tracking
                "research_questions": [],
                "answered_questions": [],
                "question_progress": {},
                "workflow_type": "traditional"  # "traditional" or "question_driven"
            }

    async def _send_websocket_message(self, chat_id: str, data: dict):
        """Send message to WebSocket client if connected"""
        if chat_id in self.active_connections:
            try:
                await self.active_connections[chat_id].send_text(json.dumps(data))
                print(f"Sent WebSocket message to {chat_id}: {data}")
            except Exception as e:
                print(f"Failed to send WebSocket message: {e}")
                if chat_id in self.active_connections:
                    del self.active_connections[chat_id]
        else:
            print(f"No WebSocket connection for chat {chat_id}")

    async def _notify_stream_clients(self, chat_id: str, data_type: str):
        """Notify streaming clients of data updates"""
        if self.stream_manager:
            try:
                if data_type == "tasks":
                    tasks_data = await self.get_agent_tasks(chat_id)
                    await self.stream_manager.notify_tasks_update(chat_id, tasks_data)
                elif data_type == "operations":
                    operations_data = await self.get_agent_operations(chat_id)
                    await self.stream_manager.notify_operations_update(chat_id, operations_data)
                elif data_type == "comms":
                    comms_data = await self.get_agent_comms(chat_id)
                    await self.stream_manager.notify_comms_update(chat_id, comms_data)
                elif data_type == "questions":
                    questions_data = await self.get_research_questions(chat_id)
                    await self.stream_manager.notify_questions_update(chat_id, questions_data)
            except Exception as e:
                print(f"Error notifying stream clients for {data_type}: {e}")

    async def add_agent_conversation(self, chat_id: str, from_agent: str, to_agent: str, message: str, conversation_type: str = "chat", context: dict = None):
        """Add agent-to-agent conversation to COMMS stream"""
        self._initialize_chat_state(chat_id)
        
        # Enhanced formatting for question-driven conversations
        if conversation_type in ["question_research", "question_analysis", "question_synthesis"]:
            question_context = context.get("question_context") if context else None
            if question_context:
                formatted_message = f"{from_agent} → {to_agent} (Q: {question_context[:50]}...): {message}"
            else:
                formatted_message = f"{from_agent} → {to_agent} [Question Research]: {message}"
        else:
            # Standard formatting
            formatted_message = f"{from_agent} → {to_agent}: {message}"
        
        comm_entry = {
            "id": len(_research_storage[chat_id]["comms"]) + 1,
            "from_agent": from_agent,
            "to_agent": to_agent, 
            "message": formatted_message,
            "raw_message": message,  # Store original message too
            "conversation_type": conversation_type,
            "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "type": "agent_conversation"
        }
        
        # Add context data if provided
        if context:
            comm_entry["context"] = context
        
        _research_storage[chat_id]["comms"].append(comm_entry)
        
        # Keep comms manageable 
        if len(_research_storage[chat_id]["comms"]) > 100:
            _research_storage[chat_id]["comms"] = _research_storage[chat_id]["comms"][-100:]
            
        await self._notify_stream_clients(chat_id, "comms")
        
        # Also send via WebSocket
        await self._send_websocket_message(chat_id, {
            "event": "agent_conversation",
            "data": comm_entry
        })

    async def add_agent_operation(self, chat_id: str, agent: str, operation_type: str, title: str, details: str, status: str = "active", progress: int = 0, data: Dict = None):
        """Add agent workspace activity to OPERATIONS stream"""
        self._initialize_chat_state(chat_id)
        
        operation_entry = {
            "id": len(_research_storage[chat_id]["operations"]) + 1,
            "agent": agent,
            "operation_type": operation_type,  # 'searching', 'analyzing', 'composing', 'reading', 'question_research'
            "title": title,
            "details": details,
            "status": status,  # 'active', 'completed', 'paused', 'error'
            "progress": progress,  # 0-100
            "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "data": data or {}
        }
        
        _research_storage[chat_id]["operations"].append(operation_entry)
        
        # Keep operations manageable
        if len(_research_storage[chat_id]["operations"]) > 50:
            _research_storage[chat_id]["operations"] = _research_storage[chat_id]["operations"][-50:]
            
        await self._notify_stream_clients(chat_id, "operations")
        
        # Also send via WebSocket  
        await self._send_websocket_message(chat_id, {
            "event": "agent_operation",
            "data": operation_entry
        })

    async def update_agent_operation(self, chat_id: str, operation_id: int, status: str = None, progress: int = None, details: str = None, data: Dict = None):
        """Update an existing operation"""
        self._initialize_chat_state(chat_id)
        
        for operation in _research_storage[chat_id]["operations"]:
            if operation["id"] == operation_id:
                if status is not None:
                    operation["status"] = status
                if progress is not None:
                    operation["progress"] = progress  
                if details is not None:
                    operation["details"] = details
                if data is not None:
                    operation["data"].update(data)
                    
                await self._notify_stream_clients(chat_id, "operations")
                break

    # NEW: Question-driven research methods with task integration
    
    async def set_research_questions(self, chat_id: str, questions: List[Dict[str, Any]]):
        """Set the research questions for question-driven workflow and create question tasks"""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]
        
        current_state["research_questions"] = questions
        current_state["workflow_type"] = "question_driven"
        
        # Create individual question tasks
        question_tasks = []
        for i, q in enumerate(questions, 1):
            question_text = q.get("question", f"Research Question {i}")
            category = q.get("category", "general")
            
            question_task = {
                "id": i,
                "title": f"Q{i}: {question_text[:60]}{'...' if len(question_text) > 60 else ''}",
                "full_question": question_text,
                "status": "pending",
                "type": "research_question",
                "category": category,
                "question_id": i,
                "progress": 0,
                "current_phase": "queued"
            }
            question_tasks.append(question_task)
            
            # Initialize question progress tracking
            current_state["question_progress"][str(i)] = {
                "status": "pending",
                "progress": 0,
                "assigned_agent": None,
                "started_at": None,
                "completed_at": None,
                "current_phase": "queued"
            }
        
        # Replace generic tasks with question tasks
        current_state["tasks"] = question_tasks
        
        # Add synthesis task
        if len(questions) > 0:
            synthesis_task = {
                "id": len(questions) + 1,
                "title": f"Final Report: Synthesize {len(questions)} research questions",
                "status": "pending",
                "type": "synthesis",
                "progress": 0
            }
            current_state["tasks"].append(synthesis_task)
        
        await self._notify_stream_clients(chat_id, "questions")
        await self._notify_stream_clients(chat_id, "tasks")
        
        # Add system message about questions
        current_state["comms"].append({
            "id": len(current_state["comms"]) + 1,
            "agent": "SYSTEM",
            "message": f"📋 Research questions generated: {len(questions)} questions ready for systematic investigation",
            "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "type": "system_announcement",
            "question_count": len(questions)
        })
        await self._notify_stream_clients(chat_id, "comms")

    async def update_question_progress(self, chat_id: str, question_id: int, 
                                     status: str = None, progress: int = None, 
                                     assigned_agent: str = None):
        """Update progress for a specific research question and corresponding task"""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]
        
        question_key = str(question_id)
        if question_key in current_state["question_progress"]:
            q_progress = current_state["question_progress"][question_key]
            
            if status is not None:
                q_progress["status"] = status
                if status == "active" and q_progress["started_at"] is None:
                    q_progress["started_at"] = datetime.now().isoformat()
                elif status == "completed":
                    q_progress["completed_at"] = datetime.now().isoformat()
                    
            if progress is not None:
                q_progress["progress"] = progress
                
            if assigned_agent is not None:
                q_progress["assigned_agent"] = assigned_agent
            
            # Update corresponding task
            for task in current_state["tasks"]:
                if task.get("question_id") == question_id:
                    if status == "active":
                        task["status"] = "in-progress"
                        task["title"] = f"🔍 Q{question_id}: {task.get('full_question', '')[:50]}..."
                        task["current_phase"] = "researching"
                    elif status == "completed":
                        task["status"] = "completed"
                        task["progress"] = 100
                        task["title"] = f"✅ Q{question_id}: {task.get('full_question', '')[:50]}..."
                        task["current_phase"] = "completed"
                    
                    if progress is not None:
                        task["progress"] = progress
                    break
            
            await self._notify_stream_clients(chat_id, "questions")
            await self._notify_stream_clients(chat_id, "tasks")

    async def add_answered_question(self, chat_id: str, question_data: Dict[str, Any]):
        """Add a completed question with its answer"""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]
        
        # Add timestamp
        question_data["answered_at"] = datetime.now().isoformat()
        
        current_state["answered_questions"].append(question_data)
        
        # Update progress tracking
        question_id = question_data.get("question_id", question_data.get("id"))
        if question_id:
            await self.update_question_progress(chat_id, question_id, "completed", 100)
        
        await self._notify_stream_clients(chat_id, "questions")
        
        # Add completion message to comms
        question_text = question_data.get("question", "Research question")
        summary = question_data.get("summary", "answered")
        current_state["comms"].append({
            "id": len(current_state["comms"]) + 1,
            "agent": "SYSTEM",
            "message": f"✅ Question #{question_id} completed: {question_text[:50]}... - {summary}",
            "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "type": "question_completion",
            "question_id": question_id
        })
        await self._notify_stream_clients(chat_id, "comms")

    async def get_research_questions(self, chat_id: str) -> Dict[str, Any]:
        """Get research questions and their progress"""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]
        
        return {
            "questions": current_state["research_questions"],
            "answered_questions": current_state["answered_questions"],
            "progress": current_state["question_progress"],
            "workflow_type": current_state["workflow_type"],
            "total_questions": len(current_state["research_questions"]),
            "completed_questions": len(current_state["answered_questions"])
        }

    # Helper methods for question task management
    async def start_question_research(self, chat_id: str, question_id: int, agent_name: str):
        """Mark a question as actively being researched"""
        await self.update_question_progress(chat_id, question_id, "active", 10, agent_name)

    async def complete_question(self, chat_id: str, question_id: int):
        """Mark a question as completed"""
        await self.update_question_progress(chat_id, question_id, "completed", 100)

    async def update_frontend_state(self, chat_id: str, agent_update: Dict[str, Any]):
        """
        UPDATED: Routes different types of updates to appropriate streams
        Enhanced with question-driven research events and task integration
        """
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]

        # Send WebSocket message to frontend
        await self._send_websocket_message(chat_id, agent_update)

        event_type = agent_update.get("event")
        needs_comms_update = False
        needs_tasks_update = False
        needs_operations_update = False
        needs_questions_update = False

        # QUESTION-DRIVEN RESEARCH EVENTS WITH TASK UPDATES
        if event_type == "research_question_started":
            question_number = agent_update.get("question_number", "?")
            question = agent_update.get("question", "Research question")
            agent_name = agent_update.get("agent", "CENTURION")
            
            # Update question progress and corresponding task
            await self.start_question_research(chat_id, question_number, agent_name)
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM",
                "message": f"🔍 Starting Question #{question_number}: {question[:60]}...",
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "question_start",
                "question_id": question_number
            })
            needs_comms_update = True
            needs_questions_update = True
            needs_tasks_update = True

        elif event_type == "research_question_completed":
            question_number = agent_update.get("question_number", "?")
            summary = agent_update.get("summary", "completed")
            
            # Update question progress and corresponding task
            await self.complete_question(chat_id, question_number)
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM",
                "message": f"✅ Question #{question_number} completed: {summary}",
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "question_completion",
                "question_id": question_number
            })
            needs_comms_update = True
            needs_questions_update = True
            needs_tasks_update = True

        elif event_type == "question_progress":
            question_id = agent_update.get("question_id")
            progress = agent_update.get("progress", 0)
            status = agent_update.get("status", "active")
            agent_name = agent_update.get("agent", "AGENT")
            
            if question_id:
                await self.update_question_progress(chat_id, question_id, status, progress, agent_name)
                needs_questions_update = True
                needs_tasks_update = True

        elif event_type == "question_assigned":
            question_id = agent_update.get("question_id")
            question = agent_update.get("question", "")
            assigned_agent = agent_update.get("assigned_agent", "")
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "CONSUL",
                "message": f"📋 Question #{question_id} assigned to {assigned_agent}: {question[:50]}...",
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "question_assignment"
            })
            needs_comms_update = True

        elif event_type == "workflow_progress":
            completed = agent_update.get("completed_questions", 0)
            total = agent_update.get("total_questions", 0)
            progress_msg = agent_update.get("message", f"Progress: {completed}/{total}")
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM", 
                "message": f"📊 {progress_msg}",
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "workflow_progress"
            })
            needs_comms_update = True

        # CONSUL CONVERSATION EVENTS → COMMS
        elif event_type == "consul_thinking":
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "CONSUL",
                "message": agent_update.get("message", "CONSUL: Thinking..."),
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "thinking"
            })
            needs_comms_update = True
            
        elif event_type == "consul_response":
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": agent_update.get("agent", "CONSUL"),
                "message": agent_update.get("message", ""),
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "response",
                "requires_response": agent_update.get("requires_response", False)
            })
            needs_comms_update = True
            
            if agent_update.get("mission_plan"):
                current_state["consul_conversation"]["plan"] = agent_update["mission_plan"]
            
            # NEW: Handle research questions in consul response
            if agent_update.get("research_questions"):
                await self.set_research_questions(chat_id, agent_update["research_questions"])
                needs_questions_update = True
                needs_tasks_update = True

        # AGENT-TO-AGENT CONVERSATIONS → COMMS  
        elif event_type == "agent_conversation":
            from_agent = agent_update.get("from_agent", "UNKNOWN")
            to_agent = agent_update.get("to_agent", "UNKNOWN") 
            message = agent_update.get("message", "")
            conversation_type = agent_update.get("conversation_type", "chat")
            
            # Enhanced formatting for question-driven conversations
            if conversation_type in ["question_research", "question_analysis", "question_synthesis"]:
                question_context = agent_update.get("question_context", "")
                if question_context:
                    formatted_message = f"{from_agent} → {to_agent} (Q: {question_context[:40]}...): {message}"
                else:
                    formatted_message = f"{from_agent} → {to_agent} [Question Research]: {message}"
            else:
                # Standard formatting
                formatted_message = f"{from_agent} → {to_agent}: {message}"
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message": formatted_message,
                "raw_message": message,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "agent_conversation",
                "conversation_type": conversation_type,
                "task_id": agent_update.get("task_id"),
                "question_context": agent_update.get("question_context")
            })
            needs_comms_update = True

        # AGENT OPERATIONS → OPERATIONS
        elif event_type == "agent_operation":
            agent = agent_update.get("agent", "UNKNOWN")
            operation_type = agent_update.get("operation_type", "unknown")
            title = agent_update.get("title", "Working...")
            details = agent_update.get("details", "")
            status = agent_update.get("status", "active")
            progress = agent_update.get("progress", 0)
            
            current_state["operations"].append({
                "id": len(current_state["operations"]) + 1,
                "agent": agent,
                "operation_type": operation_type,
                "title": title, 
                "details": details,
                "status": status,
                "progress": progress,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "data": agent_update.get("data", {})
            })
            needs_operations_update = True

        # SYSTEM EVENTS → COMMS (but also update other streams as needed)
        elif event_type == "mission_approved":
            current_state["mission_state"] = "APPROVED"
            
            # Check if this is question-driven workflow
            workflow_type = "question-driven" if current_state.get("research_questions") else "traditional"
            
            approval_message = f"Mission approved! Starting {workflow_type} research workflow."
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM",
                "message": approval_message,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "system_announcement",
                "workflow_type": workflow_type
            })
            needs_comms_update = True
            
            # Update tasks based on workflow type (only if not already question tasks)
            if workflow_type == "traditional":
                current_state["tasks"] = [
                    {"id": 1, "title": "Mission approved - preparing execution", "status": "in-progress", "type": "planning"}
                ]
                needs_tasks_update = True
            # For question-driven, tasks are already set by set_research_questions()
            
        elif event_type == "mission_initiated":
            current_state["mission_state"] = "ACTIVE"
            workflow_type = current_state.get("workflow_type", "traditional")
            
            initiation_message = f"Mission initiated with {workflow_type} research methodology."
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM",
                "message": initiation_message,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "system_announcement"
            })
            needs_comms_update = True
            
            # Update tasks based on workflow type (only if not already question tasks)
            if workflow_type == "traditional":
                current_state["tasks"] = [
                    {"id": 1, "title": "Data collection phase", "status": "in-progress", "type": "research"},
                    {"id": 2, "title": "Analysis phase", "status": "pending", "type": "analysis"},
                    {"id": 3, "title": "Report generation", "status": "pending", "type": "deliverable"}
                ]
                needs_tasks_update = True
            # For question-driven, individual question tasks are already active

        # WORKFLOW STEP EVENTS → BOTH COMMS AND OPERATIONS
        elif event_type in ["workflow_step_started", "workflow_step_completed"]:
            agent = agent_update.get("agent_name", "SYSTEM")
            step_number = agent_update.get("step_number", "?")
            message = agent_update.get("message", "")
            
            # Enhanced messaging for question-driven workflows
            workflow_type = current_state.get("workflow_type", "traditional")
            if workflow_type == "question-driven":
                if event_type == "workflow_step_started":
                    if "question" in message.lower():
                        formatted_message = f"🔍 Step {step_number}: Starting question research phase"
                    else:
                        formatted_message = f"🚀 Step {step_number}: {message}"
                else:
                    formatted_message = f"✅ Step {step_number}: {message}"
            else:
                # Traditional formatting
                if event_type == "workflow_step_started":
                    formatted_message = f"🚀 Step {step_number}: {message}"
                else:
                    formatted_message = f"✅ Step {step_number}: {message}"
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": agent,
                "message": formatted_message,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "workflow_announcement",
                "step_number": step_number,
                "workflow_type": workflow_type
            })
            needs_comms_update = True

        # DELIVERABLE EVENTS → STORAGE
        elif event_type == "new_deliverable":
            deliverable = agent_update.get("deliverable")
            if deliverable:
                # Add to deliverables storage
                current_state["deliverables"].append(deliverable)
                print(f"Added deliverable to storage: {deliverable.get('title', 'Unknown')}")
                
                # Enhanced messaging for question-driven deliverables
                deliverable_title = deliverable.get('title', 'New Document')
                workflow_type = current_state.get("workflow_type", "traditional")
                
                if workflow_type == "question-driven":
                    question_count = len(current_state.get("answered_questions", []))
                    message = f"📄 Question-driven report complete: {deliverable_title} (synthesized from {question_count} research questions)"
                else:
                    message = f"📄 Created deliverable: {deliverable_title}"
                
                current_state["comms"].append({
                    "id": len(current_state["comms"]) + 1,
                    "agent": "SCRIBE",
                    "message": message,
                    "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                    "type": "deliverable_announcement",
                    "workflow_type": workflow_type
                })
                needs_comms_update = True

        elif event_type == "deliverable_update":
            deliverable = agent_update.get("deliverable")
            if deliverable:
                # Update existing deliverable or add if not found
                title = deliverable.get("title", "")
                found = False
                for i, existing in enumerate(current_state["deliverables"]):
                    if existing.get("title") == title:
                        current_state["deliverables"][i] = deliverable
                        found = True
                        break
                
                if not found:
                    current_state["deliverables"].append(deliverable)
                
                print(f"Updated deliverable in storage: {title}")

        # Handle mission completion with enhanced question-driven support
        elif event_type == "mission_complete":
            current_state["mission_state"] = "COMPLETED"
            
            # Get actual deliverable count and question stats
            actual_deliverable_count = len(current_state["deliverables"])
            workflow_type = current_state.get("workflow_type", "traditional")
            
            if workflow_type == "question-driven":
                total_questions = len(current_state.get("research_questions", []))
                answered_questions = len(current_state.get("answered_questions", []))
                completion_message = f"Question-driven research mission completed! {answered_questions}/{total_questions} questions answered, {actual_deliverable_count} deliverable(s) generated."
                completion_data = {
                    "deliverable_count": actual_deliverable_count,
                    "total_questions": total_questions,
                    "answered_questions": answered_questions,
                    "completion_time": agent_update.get("completion_time"),
                    "workflow_type": "question-driven"
                }
                
                # Update synthesis task to completed
                for task in current_state["tasks"]:
                    if task.get("type") == "synthesis":
                        task["status"] = "completed"
                        task["progress"] = 100
                        break
            else:
                completion_message = agent_update.get("message", "Traditional research mission completed.")
                completion_data = {
                    "deliverable_count": actual_deliverable_count,
                    "completion_time": agent_update.get("completion_time"),
                    "workflow_type": "traditional"
                }
            
            current_state["comms"].append({
                "id": len(current_state["comms"]) + 1,
                "agent": "SYSTEM",
                "message": completion_message,
                "time": datetime.now().replace(microsecond=0).isoformat() + "Z",
                "type": "system_announcement",
                "completion_data": completion_data
            })
            needs_comms_update = True
            
            # Update all tasks to completed
            for task in current_state["tasks"]:
                if task["status"] != "completed":
                    task["status"] = "completed"
                    task["progress"] = 100
                    
            completion_task_exists = any(task.get("type") == "completion" for task in current_state["tasks"])
            if not completion_task_exists:
                current_state["tasks"].append({
                    "id": len(current_state["tasks"]) + 1,
                    "title": f"Mission completed successfully ({workflow_type})",
                    "status": "completed",
                    "type": "completion",
                    "completion_time": agent_update.get("completion_time"),
                    "workflow_type": workflow_type
                })
            needs_tasks_update = True

        # Keep data manageable
        if len(current_state["comms"]) > 100:
            current_state["comms"] = current_state["comms"][-100:]
        if len(current_state["operations"]) > 50:
            current_state["operations"] = current_state["operations"][-50:]
        
        # Notify streaming clients
        if needs_comms_update:
            await self._notify_stream_clients(chat_id, "comms")
        if needs_tasks_update:
            await self._notify_stream_clients(chat_id, "tasks")
        if needs_operations_update:
            await self._notify_stream_clients(chat_id, "operations")
        if needs_questions_update:
            await self._notify_stream_clients(chat_id, "questions")
        
        await asyncio.sleep(0.1)

    # Existing getter methods remain the same
    async def get_agent_tasks(self, chat_id: str) -> List[dict]:
        """Transform ADK workflow states to frontend tasks format."""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["tasks"]

    async def get_agent_operations(self, chat_id: str) -> List[dict]:
        """Get agent workspace operations (what they're actively doing)"""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["operations"]

    async def get_agent_comms(self, chat_id: str) -> List[dict]:
        """Get agent conversations (actual chat between agents)"""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["comms"]

    async def get_deliverables(self, chat_id: str) -> List[dict]:
        """Get deliverables for a chat."""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["deliverables"]

    async def get_consul_conversation(self, chat_id: str) -> Dict[str, Any]:
        """Get Consul conversation state for a chat."""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["consul_conversation"]

    async def update_consul_conversation(self, chat_id: str, stage: str, data: Dict[str, Any] = None):
        """Update Consul conversation state."""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]["consul_conversation"]
        current_state["stage"] = stage
        
        if data:
            current_state.update(data)

    async def get_mission_state(self, chat_id: str) -> str:
        """Get the current mission state for a chat."""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id]["mission_state"]

    async def set_mission_state(self, chat_id: str, state: str):
        """Set the mission state for a chat."""
        self._initialize_chat_state(chat_id)
        _research_storage[chat_id]["mission_state"] = state

    # NEW: Question-driven research getters
    async def get_workflow_type(self, chat_id: str) -> str:
        """Get the workflow type (traditional or question_driven)"""
        self._initialize_chat_state(chat_id)
        return _research_storage[chat_id].get("workflow_type", "traditional")

    async def get_question_workflow_status(self, chat_id: str) -> Dict[str, Any]:
        """Get comprehensive status of question-driven workflow"""
        self._initialize_chat_state(chat_id)
        current_state = _research_storage[chat_id]
        
        total_questions = len(current_state.get("research_questions", []))
        answered_questions = len(current_state.get("answered_questions", []))
        
        # Calculate overall progress
        overall_progress = int((answered_questions / total_questions) * 100) if total_questions > 0 else 0
        
        return {
            "workflow_type": current_state.get("workflow_type", "traditional"),
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "remaining_questions": total_questions - answered_questions,
            "overall_progress": overall_progress,
            "question_progress": current_state.get("question_progress", {}),
            "mission_state": current_state.get("mission_state", "PENDING")
        }

# Global instance of StateManager to be used across the application
state_manager = StateManager()