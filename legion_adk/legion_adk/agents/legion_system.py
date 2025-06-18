import os
from typing import List, Dict, Any
from datetime import datetime

# Import ADK components
from services.adk_orchestrator import ADKWorkflowOrchestrator
from services.adk_communication import get_communication_manager
from services.state_manager import StateManager

# Import ADK agents
from agents.consul import ConsulADKAgent
from agents.centurion import CenturionADKAgent
from agents.augur import AugurADKAgent
from agents.scribe import ScribeADKAgent

class LegionADKSystem:
    """Streamlined Legion system with ADK orchestration and agent-to-agent communication"""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.orchestrator = ADKWorkflowOrchestrator(state_manager)
        self.communication_manager = get_communication_manager(state_manager)

        # Get API keys from environment variables
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        sonar_api_key = os.getenv('SONAR_API_KEY')
        
        if not gemini_api_key:
            print("WARNING: GEMINI_API_KEY not found in environment variables")
        if not sonar_api_key:
            print("WARNING: SONAR_API_KEY not found in environment variables")
            
        # Initialize ADK agents
        self.consul = ConsulADKAgent(self.state_manager, api_key=gemini_api_key)
        self.centurion = CenturionADKAgent(self.state_manager, sonar_api_key=sonar_api_key, gemini_api_key=gemini_api_key)
        self.augur = AugurADKAgent(self.state_manager, api_key=gemini_api_key)
        self.scribe = ScribeADKAgent(self.state_manager, api_key=gemini_api_key)

        # Register all agents with the ADK orchestrator
        self.orchestrator.register_agent("consul", self.consul)
        self.orchestrator.register_agent("centurion", self.centurion)
        self.orchestrator.register_agent("augur", self.augur)
        self.orchestrator.register_agent("scribe", self.scribe)

        print("LEGION ADK SYSTEM: Initialized with streamlined agent collaboration")

    async def start_mission_with_context(self, chat_id: str, mission_context: Dict[str, Any]):
        """Start ADK workflow with mission context"""
        research_focus = mission_context.get("research_focus", "research topic")
        mission_plan = mission_context.get("mission_plan", {})
        
        print(f"LEGION ADK SYSTEM: Starting workflow for chat {chat_id}")

        try:
            await self.state_manager.add_agent_conversation(
                chat_id=chat_id,
                from_agent="SYSTEM",
                to_agent="ALL_AGENTS",
                message=f"🚀 Mission initiated: {mission_plan.get('mission_title', research_focus)}",
                conversation_type="system_announcement",
                context={
                    "mission_type": "question_driven_research",
                    "research_focus": research_focus,
                    "objectives_count": len(mission_plan.get("objectives", [])),
                    "agents_involved": ["CONSUL", "CENTURION", "AUGUR", "SCRIBE"]
                }
            )

            # Execute workflow
            workflow_results = await self.orchestrator.execute_workflow_with_context(
                "question_driven_research", 
                chat_id, 
                mission_context
            )

            # Check deliverables
            deliverables = await self.state_manager.get_deliverables(chat_id)
            
            if deliverables and len(deliverables) > 0:
                await self.state_manager.add_agent_conversation(
                    chat_id=chat_id,
                    from_agent="SYSTEM",
                    to_agent="ALL_AGENTS",
                    message=f"✅ Mission completed successfully! Generated {len(deliverables)} deliverable(s)",
                    conversation_type="system_announcement",
                    context={
                        "research_focus": research_focus,
                        "deliverable_count": len(deliverables),
                        "completion_time": datetime.now().isoformat()
                    }
                )
                
                await self.state_manager.update_frontend_state(
                    chat_id,
                    {
                        "event": "mission_complete",
                        "message": f"Research mission completed: {len(deliverables)} deliverable(s) ready",
                        "mission_status": "COMPLETED",
                        "deliverable_count": len(deliverables),
                        "completion_time": datetime.now().replace(microsecond=0).isoformat() + "Z"
                    }
                )
            else:
                await self.state_manager.add_agent_conversation(
                    chat_id=chat_id,
                    from_agent="SYSTEM",
                    to_agent="ALL_AGENTS",
                    message="⚠️ Mission completed but no deliverables were generated",
                    conversation_type="system_announcement"
                )

        except Exception as e:
            await self.state_manager.add_agent_conversation(
                chat_id=chat_id,
                from_agent="SYSTEM",
                to_agent="ALL_AGENTS",
                message=f"❌ Mission failed: {str(e)}",
                conversation_type="system_announcement",
                context={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            
            await self.state_manager.update_frontend_state(
                chat_id,
                {
                    "event": "adk_workflow_error",
                    "message": f"ADK Workflow execution failed: {str(e)}",
                    "error_time": datetime.now().replace(microsecond=0).isoformat() + "Z"
                }
            )

    async def get_mission_status(self, chat_id: str) -> Dict[str, Any]:
        """Get comprehensive mission status"""
        consul_state = getattr(self.consul, 'conversations', {}).get(chat_id, {})
        active_workflows = self.orchestrator.list_active_workflows(chat_id)
        mission_state = await self.state_manager.get_mission_state(chat_id)
        tasks = await self.state_manager.get_agent_tasks(chat_id)
        deliverables = await self.state_manager.get_deliverables(chat_id)
        comms = await self.state_manager.get_agent_comms(chat_id)
        operations = await self.state_manager.get_agent_operations(chat_id)

        # Agent status
        agent_status = {}
        for agent_name in ["consul", "centurion", "augur", "scribe"]:
            recent_operations = [op for op in operations if op.get("agent", "").lower() == agent_name]
            
            agent_status[agent_name] = {
                "name": agent_name.upper(),
                "status": "active" if recent_operations else "ready",
                "recent_operations": len(recent_operations),
                "capabilities": self._get_agent_capabilities(agent_name)
            }

        return {
            "chat_id": chat_id,
            "system_type": "ADK_Legion_Streamlined",
            "timestamp": datetime.now().isoformat(),
            
            # Core status
            "mission_state": mission_state,
            "conversation_stage": consul_state.get("stage", "initial"),
            "plan_approved": consul_state.get("plan_ready", False),
            "mission_plan": consul_state.get("mission_plan"),
            
            # Counts
            "counts": {
                "active_workflows": len(active_workflows),
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.get("status") == "completed"]),
                "deliverables": len(deliverables),
                "conversations": len(comms),
                "operations": len(operations)
            },
            
            # Agent data
            "agents": agent_status,
            
            # Workflow data
            "workflows": {
                "active": active_workflows,
                "estimated_completion": self._estimate_completion(operations)
            },
            
            # Recent activity
            "recent_conversations": comms[-5:] if comms else [],
            "active_operations": [op for op in operations if op.get("status") == "active"],
            
            # Deliverables
            "deliverables": deliverables,
            
            # System capabilities
            "adk_features": {
                "orchestration": True,
                "a2a_communication": True,
                "question_driven_research": True,
                "intelligent_clarifications": True
            }
        }

    def _get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get agent capabilities"""
        capabilities_map = {
            "consul": ["strategic_planning", "mission_coordination", "intelligent_clarifications"],
            "centurion": ["data_collection", "web_research", "source_analysis"],
            "augur": ["comprehensive_analysis", "pattern_recognition", "insight_generation"],
            "scribe": ["content_generation", "report_writing", "synthesis"]
        }
        return capabilities_map.get(agent_name, ["general_assistance"])

    def _estimate_completion(self, operations: List[Dict]) -> str:
        """Estimate completion time based on active operations"""
        active_operations = [op for op in operations if op.get("status") == "active"]
        if not active_operations:
            return "no_active_work"
        elif len(active_operations) > 3:
            return "5-10 minutes"
        elif len(active_operations) > 1:
            return "2-5 minutes"
        else:
            return "1-2 minutes"

    async def get_adk_capabilities(self) -> Dict[str, Any]:
        """Return ADK system capabilities"""
        return {
            "system_name": "Legion ADK System Streamlined",
            "version": "2.0.0-streamlined",
            "features": {
                "question_driven_research": True,
                "intelligent_clarifications": True,
                "streamlined_workflow": True,
                "a2a_communication": True
            },
            "agents": {
                "consul": {
                    "role": "Strategic Mission Planner & Intelligent Coordinator",
                    "capabilities": self._get_agent_capabilities("consul")
                },
                "centurion": {
                    "role": "Data Collection & Research Specialist", 
                    "capabilities": self._get_agent_capabilities("centurion")
                },
                "augur": {
                    "role": "Comprehensive Analysis Specialist",
                    "capabilities": self._get_agent_capabilities("augur")
                },
                "scribe": {
                    "role": "Content Generation & Synthesis Specialist",
                    "capabilities": self._get_agent_capabilities("scribe")
                }
            }
        }

# Backward compatibility
LegionSystem = LegionADKSystem