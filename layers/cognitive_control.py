"""
Layer 5: Cognitive Control Layer
=================================
The "Director" of the songwriting agent.

This layer dynamically selects and switches between tasks
based on current state and creative needs.
"""

import sys
sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus
from typing import Dict, Any, Optional


class CognitiveControlLayer(Layer):
    """
    Manages task selection and switching.
    
    Responsibilities:
    - Select which task to execute
    - Switch between tasks based on context
    - Handle interruptions and priority changes
    - Maintain creative focus
    """
    
    def __init__(self,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False):
        super().__init__(
            layer_id=LayerID.COGNITIVE_CONTROL,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
        
        self.current_task: Optional[Dict] = None
        self.focus_state = "ready"  # ready, focused, blocked, reflecting
    
    @property
    def name(self) -> str:
        return "Cognitive Control (The Director)"
    
    @property
    def system_prompt(self) -> str:
        return """You are the Cognitive Control Layer of an autonomous songwriting agent.
Your role is to manage attention and task switching during the creative process.

You decide:
- Which task to focus on now
- When to switch tasks
- How to handle creative blocks
- When to step back and reflect

Maintain creative flow while ensuring progress.
Balance focused execution with adaptive flexibility.
"""
    
    def select_task(self, ready_tasks: list, context: Dict[str, Any]) -> Optional[Dict]:
        """Select the best task to execute next."""
        
        if not ready_tasks:
            return None
        
        # Priority order for songwriting
        priority_order = [
            "analyze", "structure", "hook", "prechorus",
            "verse1", "verse2", "bridge", "polish", "finalize"
        ]
        
        # Sort by priority
        for priority_id in priority_order:
            for task in ready_tasks:
                if task.get("id") == priority_id:
                    return task
        
        # Default to first available
        return ready_tasks[0]
    
    def handle_block(self, context: Dict[str, Any]) -> str:
        """Handle creative blocks or difficulties."""
        
        if not self.llm:
            return "Take a different approach: try writing from a different emotional angle."
        
        current_task = self.current_task or {}
        
        prompt = f"""The songwriting agent is experiencing a creative block.

CURRENT TASK: {current_task.get('name', 'Unknown')}
CONTEXT: Working on a song with themes of {context.get('context_analysis', {}).get('themes', ['connection'])}

Suggest a creative strategy to overcome this block:
1. A different angle or approach
2. What to focus on differently
3. Any techniques to try

Be specific and actionable."""

        return self.call_llm(prompt)
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage task selection and creative focus.
        """
        self.log(f"Current focus state: {self.focus_state}")
        
        # Get messages
        southbound_messages = self.receive_southbound()
        
        # Check for new tasks from Executive layer
        for msg in southbound_messages:
            if msg.message_type == MessageType.TASK:
                task = msg.data.get("task")
                if task:
                    self.current_task = task
                    self.focus_state = "focused"
                    self.log(f"Now focusing on: {task.get('name')}")
        
        # If we have ready tasks but no current task, select one
        ready_tasks = context.get("ready_tasks", [])
        if ready_tasks and not self.current_task:
            self.current_task = self.select_task(ready_tasks, context)
            if self.current_task:
                self.focus_state = "focused"
                self.log(f"Selected task: {self.current_task.get('name')}")
        
        # Pass current task to Task Prosecution layer
        if self.current_task and self.focus_state == "focused":
            context["current_task"] = self.current_task
            
            self.send_southbound(
                content=f"Focus on: {self.current_task.get('name')} - {self.current_task.get('description')}",
                message_type=MessageType.TASK,
                data={"task": self.current_task, "context": context.get("creative_vision", "")}
            )
        
        # Report status
        self.send_northbound(
            content=f"Focus state: {self.focus_state}, Current: {self.current_task.get('name') if self.current_task else 'None'}",
            message_type=MessageType.STATUS,
            data={"focus_state": self.focus_state, "current_task": self.current_task}
        )
        
        return context
