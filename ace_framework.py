"""
ACE Framework - Autonomous Cognitive Entities
==============================================
A multi-agent cognitive architecture for autonomous songwriting.
Based on Dave Shap's ACE Framework.

This module provides the base classes for the 6-layer cognitive architecture:
- Layer 1: Aspirational (ethics, values)
- Layer 2: Global Strategy (vision, context)
- Layer 3: Agent Model (self-awareness)
- Layer 4: Executive Function (planning)
- Layer 5: Cognitive Control (task selection)
- Layer 6: Task Prosecution (execution)
"""

import os
import json
import time
import queue
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from pathlib import Path

# Try to import Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class MessageType(Enum):
    """Types of messages that flow through the buses."""
    # Northbound (status, telemetry - going UP)
    STATUS = "status"
    TELEMETRY = "telemetry"
    TASK_RESULT = "task_result"
    ERROR = "error"
    REQUEST = "request"
    
    # Southbound (directives, commands - going DOWN)
    DIRECTIVE = "directive"
    OBJECTIVE = "objective"
    TASK = "task"
    GUIDANCE = "guidance"
    MORAL_JUDGMENT = "moral_judgment"


class LayerID(Enum):
    """Identifiers for the 6 cognitive layers."""
    ASPIRATIONAL = 1
    GLOBAL_STRATEGY = 2
    AGENT_MODEL = 3
    EXECUTIVE_FUNCTION = 4
    COGNITIVE_CONTROL = 5
    TASK_PROSECUTION = 6


@dataclass
class Message:
    """
    A message that flows through the cognitive buses.
    All messages are human-readable as per ACE Framework principles.
    """
    source_layer: LayerID
    target_layer: Optional[LayerID]  # None = broadcast to all
    message_type: MessageType
    content: str  # Human-readable natural language
    data: Dict[str, Any] = field(default_factory=dict)  # Structured data
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5  # 1-10, higher = more important
    
    def to_dict(self) -> dict:
        return {
            "source": self.source_layer.name,
            "target": self.target_layer.name if self.target_layer else "BROADCAST",
            "type": self.message_type.value,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }
    
    def __str__(self) -> str:
        return f"[{self.source_layer.name}→{self.target_layer.name if self.target_layer else 'ALL'}] {self.content}"


class Bus:
    """
    Communication bus for inter-layer messaging.
    Implements a thread-safe message queue.
    """
    def __init__(self, name: str, verbose: bool = False):
        self.name = name
        self.verbose = verbose
        self._queue: queue.Queue[Message] = queue.Queue()
        self._subscribers: Dict[LayerID, List[Callable[[Message], None]]] = {}
        self._history: List[Message] = []
        self._lock = threading.Lock()
    
    def publish(self, message: Message):
        """Publish a message to the bus."""
        with self._lock:
            self._queue.put(message)
            self._history.append(message)
            if self.verbose:
                print(f"📨 {self.name}: {message}")
    
    def subscribe(self, layer_id: LayerID, callback: Callable[[Message], None]):
        """Subscribe a layer to receive messages."""
        with self._lock:
            if layer_id not in self._subscribers:
                self._subscribers[layer_id] = []
            self._subscribers[layer_id].append(callback)
    
    def get_messages(self, for_layer: LayerID, consume: bool = True) -> List[Message]:
        """Get all pending messages for a specific layer."""
        messages = []
        with self._lock:
            temp_queue = queue.Queue()
            while not self._queue.empty():
                msg = self._queue.get()
                if msg.target_layer is None or msg.target_layer == for_layer:
                    messages.append(msg)
                    if not consume:
                        temp_queue.put(msg)
                else:
                    temp_queue.put(msg)
            # Put back unconsumed messages
            while not temp_queue.empty():
                self._queue.put(temp_queue.get())
        return messages
    
    def get_recent_history(self, count: int = 10) -> List[Message]:
        """Get recent message history."""
        with self._lock:
            return self._history[-count:]


class NorthboundBus(Bus):
    """
    Carries status, telemetry, and results UPWARD through layers.
    Lower layers report to higher layers.
    """
    def __init__(self, verbose: bool = False):
        super().__init__("NORTHBOUND", verbose)


class SouthboundBus(Bus):
    """
    Carries directives, objectives, and guidance DOWNWARD through layers.
    Higher layers direct lower layers.
    """
    def __init__(self, verbose: bool = False):
        super().__init__("SOUTHBOUND", verbose)


class Layer(ABC):
    """
    Abstract base class for cognitive layers.
    Each layer processes messages and contributes to the overall cognition.
    """
    
    def __init__(self, 
                 layer_id: LayerID,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model = None,
                 verbose: bool = False):
        self.layer_id = layer_id
        self.northbound = northbound_bus
        self.southbound = southbound_bus
        self.llm = llm_model
        self.verbose = verbose
        self._state: Dict[str, Any] = {}
        self._running = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this layer."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt that defines this layer's behavior."""
        pass
    
    def log(self, message: str):
        """Log a message if verbose mode is on."""
        if self.verbose:
            print(f"🧠 [{self.name}] {message}")
    
    def send_northbound(self, 
                        content: str, 
                        message_type: MessageType = MessageType.STATUS,
                        data: Dict = None,
                        target: LayerID = None):
        """Send a message up to higher layers."""
        msg = Message(
            source_layer=self.layer_id,
            target_layer=target,
            message_type=message_type,
            content=content,
            data=data or {}
        )
        self.northbound.publish(msg)
    
    def send_southbound(self,
                        content: str,
                        message_type: MessageType = MessageType.DIRECTIVE,
                        data: Dict = None,
                        target: LayerID = None):
        """Send a message down to lower layers."""
        msg = Message(
            source_layer=self.layer_id,
            target_layer=target,
            message_type=message_type,
            content=content,
            data=data or {}
        )
        self.southbound.publish(msg)
    
    def receive_northbound(self) -> List[Message]:
        """Receive messages from the northbound bus (from lower layers)."""
        return self.northbound.get_messages(self.layer_id)
    
    def receive_southbound(self) -> List[Message]:
        """Receive messages from the southbound bus (from higher layers)."""
        return self.southbound.get_messages(self.layer_id)
    
    def call_llm(self, prompt: str, include_history: bool = True) -> str:
        """Call the LLM with the layer's system prompt."""
        if self.llm is None:
            raise RuntimeError("No LLM configured for this layer")
        
        full_prompt = f"{self.system_prompt}\n\n---\n\n{prompt}"
        
        try:
            response = self.llm.generate_content(full_prompt)
            return response.text
        except Exception as e:
            self.log(f"LLM call failed: {e}")
            return f"Error: {e}"
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for this layer.
        Called during each cognitive cycle.
        
        Args:
            context: Current state and any input data
            
        Returns:
            Updated context with this layer's contributions
        """
        pass
    
    def start(self):
        """Start this layer's processing."""
        self._running = True
        self.log("Layer started")
    
    def stop(self):
        """Stop this layer's processing."""
        self._running = False
        self.log("Layer stopped")


class ACEAgent:
    """
    The main autonomous cognitive agent.
    Orchestrates all 6 layers to work together.
    """
    
    def __init__(self, 
                 api_key: str = None,
                 verbose: bool = False,
                 output_dir: str = None):
        self.verbose = verbose
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "generated_songs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize LLM
        self.llm = None
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key and HAS_GEMINI:
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Initialize communication buses
        self.northbound = NorthboundBus(verbose=verbose)
        self.southbound = SouthboundBus(verbose=verbose)
        
        # Layers will be initialized by subclass or setup method
        self.layers: Dict[LayerID, Layer] = {}
        
        # Agent state
        self.context: Dict[str, Any] = {
            "status": "initialized",
            "current_project": None,
            "history": []
        }
        
        self._running = False
    
    def register_layer(self, layer: Layer):
        """Register a cognitive layer with the agent."""
        self.layers[layer.layer_id] = layer
        if self.verbose:
            print(f"✅ Registered layer: {layer.name}")
    
    def log(self, message: str):
        """Log a message if verbose mode is on."""
        if self.verbose:
            print(f"🤖 [ACE Agent] {message}")
    
    def cognitive_cycle(self) -> Dict[str, Any]:
        """
        Execute one full cognitive cycle through all layers.
        
        The cycle goes:
        1. TOP-DOWN: Aspirational → Task Prosecution (southbound directives)
        2. BOTTOM-UP: Task Prosecution → Aspirational (northbound status)
        3. Repeat until task is complete
        """
        self.log("Starting cognitive cycle...")
        
        # Process layers from top to bottom (southbound flow)
        for layer_id in LayerID:
            if layer_id in self.layers:
                layer = self.layers[layer_id]
                self.log(f"Processing {layer.name}...")
                self.context = layer.process(self.context)
        
        return self.context
    
    def run(self, 
            input_data: Dict[str, Any],
            max_cycles: int = 10) -> Dict[str, Any]:
        """
        Run the agent on the given input.
        
        Args:
            input_data: Initial input (transcription, circumstance, etc.)
            max_cycles: Maximum cognitive cycles before stopping
            
        Returns:
            Final context with results
        """
        self._running = True
        self.context["input"] = input_data
        self.context["status"] = "running"
        
        # Start all layers
        for layer in self.layers.values():
            layer.start()
        
        # Initial message to start processing
        self.southbound.publish(Message(
            source_layer=LayerID.ASPIRATIONAL,
            target_layer=None,
            message_type=MessageType.OBJECTIVE,
            content=f"New creative project: {input_data.get('description', 'Generate a song')}",
            data=input_data
        ))
        
        # Run cognitive cycles
        cycle = 0
        while self._running and cycle < max_cycles:
            cycle += 1
            self.log(f"=== Cognitive Cycle {cycle}/{max_cycles} ===")
            
            self.context = self.cognitive_cycle()
            
            # Check if task is complete
            if self.context.get("status") == "complete":
                self.log("Task completed!")
                break
            
            # Check for errors
            if self.context.get("status") == "error":
                self.log(f"Error occurred: {self.context.get('error')}")
                break
        
        # Stop all layers
        for layer in self.layers.values():
            layer.stop()
        
        self._running = False
        return self.context
    
    def stop(self):
        """Stop the agent."""
        self._running = False
