"""
ACE Framework Cognitive Layers
==============================
This package contains the 6 cognitive layers of the ACE Framework
adapted for autonomous songwriting.
"""

from .aspirational import AspirationalLayer
from .global_strategy import GlobalStrategyLayer
from .agent_model import AgentModelLayer
from .executive_function import ExecutiveFunctionLayer
from .cognitive_control import CognitiveControlLayer
from .task_prosecution import TaskProsecutionLayer

__all__ = [
    'AspirationalLayer',
    'GlobalStrategyLayer', 
    'AgentModelLayer',
    'ExecutiveFunctionLayer',
    'CognitiveControlLayer',
    'TaskProsecutionLayer'
]
