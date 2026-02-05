"""
Layer 4: Executive Function Layer
==================================
The "Producer" of the songwriting agent.

This layer creates detailed project plans, manages resources,
and coordinates the songwriting process.
"""

import sys
sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class ProjectTask:
    """A task in the songwriting project."""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = None
    output: Any = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "dependencies": self.dependencies or []
        }


class ExecutiveFunctionLayer(Layer):
    """
    Plans and coordinates the songwriting project.
    
    Responsibilities:
    - Break down song creation into tasks
    - Sequence tasks appropriately
    - Manage resources and time
    - Track progress and risks
    """
    
    def __init__(self,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False):
        super().__init__(
            layer_id=LayerID.EXECUTIVE_FUNCTION,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
        
        self.project_plan: List[ProjectTask] = []
        self.current_task_index = 0
    
    @property
    def name(self) -> str:
        return "Executive Function (The Producer)"
    
    @property
    def system_prompt(self) -> str:
        return """You are the Executive Function Layer of an autonomous songwriting agent.
Your role is to create and manage the project plan for songwriting.

You break down the creative process into executable tasks:
1. Analyze source material
2. Extract themes and emotions
3. Draft song structure
4. Write verses
5. Write chorus
6. Write bridge
7. Refine and polish
8. Final review

Consider dependencies and optimal sequencing.
Flag any risks that could affect the project.
"""
    
    def create_project_plan(self, context: Dict[str, Any]) -> List[ProjectTask]:
        """Create a detailed project plan for the song."""
        
        vision = context.get("creative_vision", "")
        analysis = context.get("context_analysis", {})
        
        # Standard songwriting pipeline
        tasks = [
            ProjectTask(
                id="analyze",
                name="Analyze Source Material",
                description="Deep dive into transcription/circumstance to extract all creative elements"
            ),
            ProjectTask(
                id="structure",
                name="Define Song Structure",
                description="Determine verse/chorus/bridge arrangement based on emotional arc",
                dependencies=["analyze"]
            ),
            ProjectTask(
                id="hook",
                name="Create Core Hook/Chorus",
                description="Write the central hook that captures the song's essence",
                dependencies=["structure"]
            ),
            ProjectTask(
                id="verse1",
                name="Write Verse 1",
                description="Set up the story and introduce the theme",
                dependencies=["hook"]
            ),
            ProjectTask(
                id="verse2",
                name="Write Verse 2",
                description="Develop the narrative and add depth",
                dependencies=["verse1"]
            ),
            ProjectTask(
                id="bridge",
                name="Write Bridge",
                description="Create contrast and emotional pivot",
                dependencies=["verse2"]
            ),
            ProjectTask(
                id="prechorus",
                name="Write Pre-Chorus",
                description="Build tension leading into chorus",
                dependencies=["hook"]
            ),
            ProjectTask(
                id="polish",
                name="Polish and Refine",
                description="Review all sections, improve word choices, ensure flow",
                dependencies=["verse1", "verse2", "bridge", "prechorus"]
            ),
            ProjectTask(
                id="finalize",
                name="Finalize Song",
                description="Compile all sections, add metadata, prepare output",
                dependencies=["polish"]
            )
        ]
        
        return tasks
    
    def get_next_executable_tasks(self) -> List[ProjectTask]:
        """Get tasks that are ready to execute (dependencies met)."""
        completed_ids = {t.id for t in self.project_plan if t.status == TaskStatus.COMPLETED}
        
        ready_tasks = []
        for task in self.project_plan:
            if task.status == TaskStatus.PENDING:
                deps = task.dependencies or []
                if all(dep in completed_ids for dep in deps):
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def mark_task_complete(self, task_id: str, output: Any = None):
        """Mark a task as completed."""
        for task in self.project_plan:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.output = output
                self.log(f"Task completed: {task.name}")
                break
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current project progress."""
        total = len(self.project_plan)
        completed = sum(1 for t in self.project_plan if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.project_plan if t.status == TaskStatus.IN_PROGRESS)
        
        return {
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total - completed - in_progress,
            "percent_complete": (completed / total * 100) if total > 0 else 0
        }
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage the project plan.
        """
        self.log("Managing project execution...")
        
        # Create project plan if not exists
        if not self.project_plan and "creative_vision" in context:
            self.log("Creating project plan...")
            self.project_plan = self.create_project_plan(context)
            context["project_plan"] = [t.to_dict() for t in self.project_plan]
            
            self.send_southbound(
                content=f"Project plan created with {len(self.project_plan)} tasks",
                message_type=MessageType.DIRECTIVE,
                data={"plan": context["project_plan"]}
            )
        
        # Check for task completions from context (set by Task Prosecution)
        completed_task_id = context.get("last_completed_task_id")
        if completed_task_id:
            self.mark_task_complete(completed_task_id, context.get("last_task_output"))
            # Clear the completion flag
            context["last_completed_task_id"] = None
            context["last_task_output"] = None
        
        # Get next tasks to execute
        if self.project_plan:
            ready_tasks = self.get_next_executable_tasks()
            progress = self.get_progress()
            
            context["project_progress"] = progress
            context["ready_tasks"] = [t.to_dict() for t in ready_tasks]
            
            if ready_tasks:
                # Mark first ready task as in progress
                next_task = ready_tasks[0]
                next_task.status = TaskStatus.IN_PROGRESS
                context["current_task"] = next_task.to_dict()
                
                self.send_southbound(
                    content=f"Execute task: {next_task.name}",
                    message_type=MessageType.TASK,
                    data={"task": next_task.to_dict()}
                )
                
                self.log(f"Dispatched task: {next_task.name}")
            
            # Check if all done
            if progress["completed"] == progress["total_tasks"]:
                context["status"] = "complete"
                self.log("All tasks completed!")
            else:
                self.log(f"Progress: {progress['percent_complete']:.0f}% ({progress['completed']}/{progress['total_tasks']} tasks)")
        
        return context
