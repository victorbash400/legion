# services/adk_communication.py

import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# ADK-inspired data structures
@dataclass
class A2ATask:
    """A2A Protocol Task structure"""
    task_id: str
    from_agent: str
    to_agent: str
    task_type: str
    parameters: Dict[str, Any]
    conversation_context: List[Dict[str, Any]]
    created_at: str
    chat_id: str

@dataclass
class A2AResponse:
    """A2A Protocol Response structure"""
    task_id: str
    status: str  # "completed", "in_progress", "needs_clarification", "error"
    response_data: Dict[str, Any]
    conversation_message: str
    artifacts: List[Dict[str, Any]]
    created_at: str

class AgentCapability(Enum):
    """Agent capabilities for discovery"""
    PLANNING = "planning"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    CONTENT_GENERATION = "content_generation"
    CONVERSATION = "conversation"
    QUESTION_RESEARCH = "question_research"  # New capability for question-driven research

@dataclass
class AgentCard:
    """ADK Agent Card for discovery"""
    name: str
    version: str
    capabilities: List[AgentCapability]
    description: str
    inputs: List[str]
    outputs: List[str]
    endpoint: str

class ADKCommunicationManager:
    """
    Manages A2A communication between agents with conversational capabilities.
    Implements ADK patterns while enabling Gemini-powered agent conversations.
    Enhanced with question-driven research task types.
    """
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.agent_registry: Dict[str, AgentCard] = {}
        self.active_conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.pending_tasks: Dict[str, A2ATask] = {}
        
        # Initialize agent cards
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register default LEGION agents with their capabilities"""
        
        # CONSUL Agent Card - Enhanced with question generation
        consul_card = AgentCard(
            name="consul",
            version="2.0.0",
            capabilities=[AgentCapability.PLANNING, AgentCapability.CONVERSATION, AgentCapability.QUESTION_RESEARCH],
            description="Strategic mission planner, conversation coordinator, and research question generator",
            inputs=["user_query", "mission_requirements", "research_context"],
            outputs=["mission_plan", "task_assignments", "research_questions"],
            endpoint="/agents/consul/run"
        )
        
        # CENTURION Agent Card - Enhanced with question-specific research
        centurion_card = AgentCard(
            name="centurion",
            version="2.0.0",
            capabilities=[AgentCapability.DATA_COLLECTION, AgentCapability.CONVERSATION, AgentCapability.QUESTION_RESEARCH],
            description="Multi-source data collection specialist with question-focused research",
            inputs=["research_query", "research_question", "collection_parameters", "question_context"],
            outputs=["collected_data", "source_metadata", "question_answer_data"],
            endpoint="/agents/centurion/run"
        )
        
        # AUGUR Agent Card - Enhanced with question-specific analysis
        augur_card = AgentCard(
            name="augur",
            version="2.0.0", 
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.CONVERSATION, AgentCapability.QUESTION_RESEARCH],
            description="Advanced analysis and insight generation with question-focused analytics",
            inputs=["raw_data", "analysis_requirements", "research_question", "question_context"],
            outputs=["analysis_results", "insights", "question_answers"],
            endpoint="/agents/augur/run"
        )
        
        # SCRIBE Agent Card - Enhanced with question synthesis
        scribe_card = AgentCard(
            name="scribe",
            version="2.0.0",
            capabilities=[AgentCapability.CONTENT_GENERATION, AgentCapability.CONVERSATION, AgentCapability.QUESTION_RESEARCH],
            description="Professional deliverable generation with question-answer synthesis",
            inputs=["analysis_data", "format_requirements", "answered_questions", "synthesis_context"],
            outputs=["final_deliverable", "formatted_content", "synthesized_report"],
            endpoint="/agents/scribe/run"
        )
        
        # Register all agents
        self.agent_registry["consul"] = consul_card
        self.agent_registry["centurion"] = centurion_card
        self.agent_registry["augur"] = augur_card
        self.agent_registry["scribe"] = scribe_card
    
    async def send_agent_task(self, from_agent: str, to_agent: str, 
                            task_type: str, parameters: Dict[str, Any], 
                            chat_id: str, conversation_message: str = "") -> str:
        """
        Send a task from one agent to another using A2A protocol
        Enhanced with question-driven task types
        """
        
        # Create A2A task
        task = A2ATask(
            task_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            parameters=parameters,
            conversation_context=self._get_conversation_context(chat_id, from_agent, to_agent),
            created_at=datetime.now().isoformat(),
            chat_id=chat_id
        )
        
        # Store pending task
        self.pending_tasks[task.task_id] = task
        
        # Enhanced conversation logging for question-driven tasks
        enhanced_message = self._enhance_conversation_message(conversation_message, task_type, parameters)
        
        # Log conversation to state manager
        if enhanced_message:
            await self.state_manager.update_frontend_state(
                chat_id,
                {
                    "event": "agent_conversation",
                    "from_agent": from_agent.upper(),
                    "to_agent": to_agent.upper(),
                    "message": enhanced_message,
                    "task_id": task.task_id,
                    "task_type": task_type,
                    "conversation_type": self._get_conversation_type(task_type),
                    "question_context": parameters.get("research_question") if "question" in task_type else None
                }
            )
        
        # Add to conversation history
        self._add_to_conversation(chat_id, from_agent, to_agent, enhanced_message, "task_assignment")
        
        print(f"ADK_COMM: {from_agent.upper()} → {to_agent.upper()}: {task_type} task sent (ID: {task.task_id})")
        
        return task.task_id
    
    def _enhance_conversation_message(self, original_message: str, task_type: str, parameters: Dict[str, Any]) -> str:
        """Enhance conversation messages for question-driven tasks"""
        
        if task_type == "answer_research_question":
            question = parameters.get("research_query", "research question")
            question_id = parameters.get("question_id", "")
            category = parameters.get("question_category", "")
            return f"Please research Question #{question_id} ({category}): {question}"
        
        elif task_type == "analyze_question_data":
            question = parameters.get("research_question", "research question")
            question_id = parameters.get("question_id", "")
            return f"Please analyze data to answer Question #{question_id}: {question}"
        
        elif task_type == "synthesize_question_answers":
            total_questions = parameters.get("total_questions", 0)
            return f"Please synthesize comprehensive report from {total_questions} answered research questions"
        
        elif task_type == "generate_research_questions":
            topic = parameters.get("research_focus", "research topic")
            return f"Please generate specific research questions for: {topic}"
        
        # Return original message if no enhancement needed
        return original_message or f"Please work on {task_type}"
    
    def _get_conversation_type(self, task_type: str) -> str:
        """Get conversation type based on task type"""
        
        question_task_types = {
            "answer_research_question": "question_research",
            "analyze_question_data": "question_analysis",
            "synthesize_question_answers": "question_synthesis",
            "generate_research_questions": "question_generation"
        }
        
        return question_task_types.get(task_type, "task_assignment")
    
    async def send_agent_response(self, task_id: str, status: str, 
                                response_data: Dict[str, Any], 
                                conversation_message: str, 
                                artifacts: List[Dict[str, Any]] = None) -> A2AResponse:
        """
        Send response back to requesting agent
        Enhanced with question-driven response handling
        """
        
        if task_id not in self.pending_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.pending_tasks[task_id]
        
        # Create response
        response = A2AResponse(
            task_id=task_id,
            status=status,
            response_data=response_data,
            conversation_message=conversation_message,
            artifacts=artifacts or [],
            created_at=datetime.now().isoformat()
        )
        
        # Enhanced response message for question-driven tasks
        enhanced_response = self._enhance_response_message(
            conversation_message, task.task_type, response_data, status
        )
        
        # Log conversation response
        await self.state_manager.update_frontend_state(
            task.chat_id,
            {
                "event": "agent_conversation",
                "from_agent": task.to_agent.upper(),
                "to_agent": task.from_agent.upper(),
                "message": enhanced_response,
                "task_id": task_id,
                "response_status": status,
                "conversation_type": "task_response",
                "question_context": response_data.get("question") if "question" in task.task_type else None
            }
        )
        
        # Add to conversation history
        self._add_to_conversation(task.chat_id, task.to_agent, task.from_agent, 
                                enhanced_response, "task_response")
        
        print(f"ADK_COMM: {task.to_agent.upper()} → {task.from_agent.upper()}: {status} response sent")
        
        # Remove completed task
        if status in ["completed", "error"]:
            del self.pending_tasks[task_id]
        
        return response
    
    def _enhance_response_message(self, original_message: str, task_type: str, 
                                response_data: Dict[str, Any], status: str) -> str:
        """Enhance response messages for question-driven tasks"""
        
        if task_type == "answer_research_question" and status == "completed":
            question_id = response_data.get("question_id", "")
            summary = response_data.get("summary", "Question research completed")
            return f"✅ Question #{question_id} research completed: {summary}"
        
        elif task_type == "analyze_question_data" and status == "completed":
            question_id = response_data.get("question_id", "")
            key_findings = response_data.get("key_findings", [])
            findings_text = f" - {len(key_findings)} key findings identified" if key_findings else ""
            return f"✅ Question #{question_id} analysis completed{findings_text}"
        
        elif task_type == "synthesize_question_answers" and status == "completed":
            deliverable_title = response_data.get("title", "Research Report")
            return f"✅ Final synthesis completed: {deliverable_title}"
        
        elif task_type == "generate_research_questions" and status == "completed":
            question_count = response_data.get("question_count", 0)
            return f"✅ Generated {question_count} research questions for systematic investigation"
        
        # Return original message if no enhancement needed
        return original_message or f"Task {task_type} {status}"
    
    async def request_clarification(self, task_id: str, questions: List[str], 
                                  chat_id: str) -> None:
        """
        Agent requests clarification from the task sender
        Enhanced with question-driven context
        """
        
        if task_id not in self.pending_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.pending_tasks[task_id]
        
        # Enhanced clarification context for question-driven tasks
        clarification_context = ""
        if "question" in task.task_type:
            question = task.parameters.get("research_question", task.parameters.get("research_query", ""))
            if question:
                clarification_context = f"\nRegarding research question: '{question}'\n"
        
        # Format questions into conversational message
        question_text = "\n".join([f"• {q}" for q in questions])
        clarification_message = f"I need some clarification on your request:{clarification_context}\n{question_text}"
        
        # Send clarification request
        await self.state_manager.update_frontend_state(
            chat_id,
            {
                "event": "agent_conversation",
                "from_agent": task.to_agent.upper(),
                "to_agent": task.from_agent.upper(),
                "message": clarification_message,
                "task_id": task_id,
                "conversation_type": "clarification_request",
                "questions": questions,
                "question_context": task.parameters.get("research_question") if "question" in task.task_type else None
            }
        )
        
        # Add to conversation history
        self._add_to_conversation(chat_id, task.to_agent, task.from_agent, 
                                clarification_message, "clarification_request")
        
        print(f"ADK_COMM: {task.to_agent.upper()} requested clarification from {task.from_agent.upper()}")
    
    async def send_question_progress_update(self, chat_id: str, agent_name: str, 
                                          question_id: int, progress: int, 
                                          status: str, details: str = "") -> None:
        """Send progress update for question-driven research"""
        
        progress_message = f"Question #{question_id} progress: {progress}% - {details}" if details else f"Question #{question_id}: {progress}%"
        
        await self.state_manager.update_frontend_state(
            chat_id,
            {
                "event": "question_progress",
                "agent": agent_name.upper(),
                "question_id": question_id,
                "progress": progress,
                "status": status,
                "message": progress_message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Also add to operations for tracking
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent=agent_name.upper(),
            operation_type="question_research",
            title=f"Question #{question_id}",
            details=details or f"Progress: {progress}%",
            status=status,
            progress=progress,
            data={"question_id": question_id}
        )
    
    async def send_question_completion(self, chat_id: str, agent_name: str,
                                     question_id: int, question: str, 
                                     answer_summary: str) -> None:
        """Send completion notification for answered question"""
        
        completion_message = f"✅ Question #{question_id} answered: {answer_summary}"
        
        await self.state_manager.update_frontend_state(
            chat_id,
            {
                "event": "question_completed",
                "agent": agent_name.upper(),
                "question_id": question_id,
                "question": question,
                "answer_summary": answer_summary,
                "message": completion_message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"ADK_COMM: {agent_name.upper()} completed question #{question_id}")
    
    def _get_conversation_context(self, chat_id: str, agent1: str, agent2: str) -> List[Dict[str, Any]]:
        """Get conversation history between two agents"""
        conv_key = f"{chat_id}:{agent1}:{agent2}"
        alt_key = f"{chat_id}:{agent2}:{agent1}"
        
        # Get conversation from either direction
        context = self.active_conversations.get(conv_key, [])
        context.extend(self.active_conversations.get(alt_key, []))
        
        # Sort by timestamp and return last 10 messages
        context.sort(key=lambda x: x.get('timestamp', ''))
        return context[-10:]
    
    def _add_to_conversation(self, chat_id: str, from_agent: str, to_agent: str, 
                           message: str, message_type: str):
        """Add message to conversation history"""
        conv_key = f"{chat_id}:{from_agent}:{to_agent}"
        
        if conv_key not in self.active_conversations:
            self.active_conversations[conv_key] = []
        
        self.active_conversations[conv_key].append({
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages per conversation
        if len(self.active_conversations[conv_key]) > 20:
            self.active_conversations[conv_key] = self.active_conversations[conv_key][-20:]
    
    def get_agent_capabilities(self, agent_name: str) -> Optional[AgentCard]:
        """Get agent capabilities for discovery"""
        return self.agent_registry.get(agent_name)
    
    def discover_agents_by_capability(self, capability: AgentCapability) -> List[AgentCard]:
        """Find agents with specific capability"""
        return [card for card in self.agent_registry.values() 
                if capability in card.capabilities]
    
    def get_pending_task(self, task_id: str) -> Optional[A2ATask]:
        """Get pending task by ID"""
        return self.pending_tasks.get(task_id)
    
    async def update_task_parameters(self, task_id: str, new_parameters: Dict[str, Any]) -> bool:
        """Update parameters for an existing pending task"""
        if task_id in self.pending_tasks:
            self.pending_tasks[task_id].parameters.update(new_parameters)
            print(f"ADK_COMM: Updated parameters for task {task_id}")
            return True
        else:
            print(f"ADK_COMM: Warning - task {task_id} not found for parameter update")
            return False
    
    def get_agent_conversation_history(self, chat_id: str, agent1: str, agent2: str) -> List[Dict[str, Any]]:
        """Get full conversation history between two agents"""
        return self._get_conversation_context(chat_id, agent1, agent2)
    
    async def broadcast_agent_status(self, agent_name: str, status: str, chat_id: str, message: str = ""):
        """Broadcast agent status to all other agents and frontend"""
        
        await self.state_manager.update_frontend_state(
            chat_id,
            {
                "event": "agent_status",
                "agent": agent_name.upper(),
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"ADK_COMM: {agent_name.upper()} status: {status}")
    
    # Question-driven research specific methods
    
    def get_question_research_agents(self) -> List[AgentCard]:
        """Get all agents capable of question-driven research"""
        return self.discover_agents_by_capability(AgentCapability.QUESTION_RESEARCH)
    
    async def coordinate_question_workflow(self, chat_id: str, research_questions: List[Dict[str, Any]],
                                         mission_context: Dict[str, Any]) -> Dict[str, str]:
        """Coordinate the assignment of research questions to agents"""
        
        question_assignments = {}
        
        for question in research_questions:
            question_id = question.get("id", question.get("priority", 1))
            question_text = question.get("question", "")
            category = question.get("category", "general")
            
            # Assign based on category or round-robin
            if category in ["current_state", "key_players"]:
                assigned_agent = "centurion"  # Data collection focused
            elif category in ["trends", "challenges", "market_impact"]:
                assigned_agent = "augur"  # Analysis focused  
            else:
                assigned_agent = "centurion"  # Default to data collection
            
            question_assignments[f"question_{question_id}"] = assigned_agent
            
            # Log assignment
            await self.state_manager.update_frontend_state(
                chat_id,
                {
                    "event": "question_assigned",
                    "question_id": question_id,
                    "question": question_text,
                    "assigned_agent": assigned_agent.upper(),
                    "category": category,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return question_assignments
    
    async def track_question_workflow_progress(self, chat_id: str, 
                                             total_questions: int, 
                                             completed_questions: int) -> None:
        """Track overall progress of question-driven workflow"""
        
        progress_percentage = int((completed_questions / total_questions) * 100) if total_questions > 0 else 0
        
        await self.state_manager.update_frontend_state(
            chat_id,
            {
                "event": "workflow_progress",
                "total_questions": total_questions,
                "completed_questions": completed_questions,
                "progress_percentage": progress_percentage,
                "message": f"Question research progress: {completed_questions}/{total_questions} questions answered",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"ADK_COMM: Question workflow progress: {completed_questions}/{total_questions} ({progress_percentage}%)")

# Global communication manager instance
adk_comm_manager = None

def get_communication_manager(state_manager=None):
    """Get or create global communication manager"""
    global adk_comm_manager
    if adk_comm_manager is None and state_manager:
        adk_comm_manager = ADKCommunicationManager(state_manager)
    return adk_comm_manager