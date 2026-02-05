"""
Agent Spawner - Dynamic Sub-Agent Creation
===========================================
Based on the HAAS (Hierarchical Autonomous Agent Swarm) pattern from Dave Shap.

Enables dynamic creation of task-specific sub-agents with:
- Privilege inheritance (sub-agents can't exceed parent privileges)
- Lifecycle management (create, monitor, terminate)
- Hierarchical control
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime


class AgentPrivilege(Enum):
    """Privileges that agents can have."""
    READ_CONTEXT = "read_context"
    WRITE_CONTEXT = "write_context"
    CALL_LLM = "call_llm"
    SPAWN_AGENTS = "spawn_agents"
    TERMINATE_AGENTS = "terminate_agents"
    FILE_OUTPUT = "file_output"
    FULL_ACCESS = "full_access"


@dataclass
class SubAgent:
    """A dynamically spawned sub-agent for specific tasks."""
    id: str
    name: str
    task: str
    parent_id: Optional[str]
    privileges: List[AgentPrivilege]
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    result: Any = None
    
    def has_privilege(self, privilege: AgentPrivilege) -> bool:
        """Check if agent has a specific privilege."""
        return AgentPrivilege.FULL_ACCESS in self.privileges or privilege in self.privileges


class AgentSpawner:
    """
    Manages creation and lifecycle of dynamic sub-agents.
    
    Key principles from HAAS:
    - Agents can only spawn sub-agents one level below
    - Privileges are inherited from parent (cannot exceed)
    - Parent can terminate any descendant
    """
    
    def __init__(self, llm_model=None, verbose: bool = False):
        self.llm = llm_model
        self.verbose = verbose
        self.agents: Dict[str, SubAgent] = {}
        self.agent_lineage: Dict[str, List[str]] = {}  # parent_id -> [child_ids]
    
    def log(self, message: str):
        """Log messages if verbose mode is on."""
        if self.verbose:
            print(f"🔧 [AgentSpawner] {message}")
    
    def spawn(self,
              name: str,
              task: str,
              parent_id: Optional[str] = None,
              privileges: List[AgentPrivilege] = None) -> SubAgent:
        """
        Spawn a new sub-agent for a specific task.
        
        Args:
            name: Human-readable name for the agent
            task: The task description for the agent
            parent_id: ID of parent agent (for privilege inheritance)
            privileges: Requested privileges (will be limited by parent)
            
        Returns:
            The spawned SubAgent
        """
        agent_id = str(uuid.uuid4())[:8]
        
        # Determine privileges
        if parent_id and parent_id in self.agents:
            parent = self.agents[parent_id]
            # Inherit privileges from parent (cannot exceed)
            if privileges:
                allowed_privileges = [p for p in privileges if parent.has_privilege(p)]
            else:
                allowed_privileges = parent.privileges.copy()
        else:
            # Root agent gets requested or default privileges
            allowed_privileges = privileges or [
                AgentPrivilege.READ_CONTEXT,
                AgentPrivilege.WRITE_CONTEXT,
                AgentPrivilege.CALL_LLM
            ]
        
        agent = SubAgent(
            id=agent_id,
            name=name,
            task=task,
            parent_id=parent_id,
            privileges=allowed_privileges
        )
        
        self.agents[agent_id] = agent
        
        # Track lineage
        if parent_id:
            if parent_id not in self.agent_lineage:
                self.agent_lineage[parent_id] = []
            self.agent_lineage[parent_id].append(agent_id)
        
        self.log(f"Spawned agent '{name}' (ID: {agent_id}) for task: {task[:50]}...")
        return agent
    
    def execute_agent(self, 
                      agent_id: str, 
                      context: Dict[str, Any],
                      executor: Callable[[str, Dict[str, Any]], Any] = None) -> Any:
        """
        Execute an agent's task.
        
        Args:
            agent_id: ID of the agent to execute
            context: The context to pass to the agent
            executor: Optional custom executor function
            
        Returns:
            The result of the agent's execution
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        if agent.status != "active":
            raise ValueError(f"Agent {agent_id} is not active (status: {agent.status})")
        
        self.log(f"Executing agent '{agent.name}'...")
        
        # Check privileges
        if not agent.has_privilege(AgentPrivilege.READ_CONTEXT):
            context = {}  # No context access
        
        # Execute using LLM if available and has privilege
        if self.llm and agent.has_privilege(AgentPrivilege.CALL_LLM):
            if executor:
                result = executor(agent.task, context)
            else:
                # Default LLM execution
                prompt = f"""You are a specialized sub-agent with the following task:

TASK: {agent.task}

CONTEXT:
{context}

Execute this task and provide your result."""
                
                try:
                    response = self.llm.generate_content(prompt)
                    result = response.text
                except Exception as e:
                    result = f"Error executing agent: {e}"
        else:
            result = f"Agent '{agent.name}' task defined: {agent.task}"
        
        agent.result = result
        agent.status = "completed"
        
        self.log(f"Agent '{agent.name}' completed")
        return result
    
    def terminate(self, agent_id: str, cascade: bool = True) -> bool:
        """
        Terminate an agent and optionally its descendants.
        
        Args:
            agent_id: ID of agent to terminate
            cascade: If True, also terminate all descendants
            
        Returns:
            True if terminated successfully
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.status = "terminated"
        
        self.log(f"Terminated agent '{agent.name}'")
        
        # Cascade to children
        if cascade and agent_id in self.agent_lineage:
            for child_id in self.agent_lineage[agent_id]:
                self.terminate(child_id, cascade=True)
        
        return True
    
    def get_descendants(self, agent_id: str) -> List[SubAgent]:
        """Get all descendant agents of a given agent."""
        descendants = []
        
        if agent_id in self.agent_lineage:
            for child_id in self.agent_lineage[agent_id]:
                if child_id in self.agents:
                    descendants.append(self.agents[child_id])
                    descendants.extend(self.get_descendants(child_id))
        
        return descendants
    
    def get_active_agents(self) -> List[SubAgent]:
        """Get all currently active agents."""
        return [a for a in self.agents.values() if a.status == "active"]
    
    def cleanup_completed(self) -> int:
        """Remove all completed agents. Returns count of removed agents."""
        completed_ids = [a.id for a in self.agents.values() if a.status == "completed"]
        for agent_id in completed_ids:
            del self.agents[agent_id]
        return len(completed_ids)


# Specialized agent templates for songwriting
SONGWRITER_AGENT_TEMPLATES = {
    "verse_writer": {
        "name": "Verse Writer",
        "task_template": "Write verse {verse_num} for a song about {theme}",
        "privileges": [AgentPrivilege.READ_CONTEXT, AgentPrivilege.CALL_LLM]
    },
    "chorus_writer": {
        "name": "Chorus Writer", 
        "task_template": "Write a memorable chorus for a song about {theme}",
        "privileges": [AgentPrivilege.READ_CONTEXT, AgentPrivilege.CALL_LLM]
    },
    "theme_analyst": {
        "name": "Theme Analyst",
        "task_template": "Analyze the themes and emotions in: {content}",
        "privileges": [AgentPrivilege.READ_CONTEXT, AgentPrivilege.CALL_LLM]
    },
    "cultural_advisor": {
        "name": "Cultural Advisor",
        "task_template": "Review for cultural sensitivity and suggest multilingual elements: {content}",
        "privileges": [AgentPrivilege.READ_CONTEXT, AgentPrivilege.CALL_LLM]
    },
    "quality_reviewer": {
        "name": "Quality Reviewer",
        "task_template": "Review and polish these lyrics for quality: {content}",
        "privileges": [AgentPrivilege.READ_CONTEXT, AgentPrivilege.CALL_LLM]
    }
}


def spawn_songwriter_agent(spawner: AgentSpawner, 
                           template_name: str, 
                           parent_id: str = None,
                           **kwargs) -> SubAgent:
    """
    Spawn a specialized songwriter sub-agent from template.
    
    Args:
        spawner: The AgentSpawner instance
        template_name: Name of template from SONGWRITER_AGENT_TEMPLATES
        parent_id: Optional parent agent ID
        **kwargs: Variables for the task template
        
    Returns:
        The spawned SubAgent
    """
    if template_name not in SONGWRITER_AGENT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    template = SONGWRITER_AGENT_TEMPLATES[template_name]
    task = template["task_template"].format(**kwargs)
    
    return spawner.spawn(
        name=template["name"],
        task=task,
        parent_id=parent_id,
        privileges=template["privileges"]
    )
