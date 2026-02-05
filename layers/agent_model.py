"""
Layer 3: Agent Model Layer
===========================
The "Self-Awareness" of the songwriting agent.

This layer maintains an understanding of the agent's own capabilities,
limitations, and resources.
"""

import sys
sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus
from typing import Dict, Any, List


class AgentModelLayer(Layer):
    """
    Maintains self-awareness of agent capabilities.
    
    Responsibilities:
    - Track available tools and resources
    - Know language capabilities
    - Understand creative strengths/weaknesses
    - Monitor past performance
    """
    
    def __init__(self,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False):
        super().__init__(
            layer_id=LayerID.AGENT_MODEL,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
        
        # Self-model of capabilities
        self.capabilities = {
            "languages": ["English", "Korean", "Tagalog", "Spanish", "Japanese"],
            "genres": ["pop", "ballad", "rock", "R&B", "hip-hop", "folk", "K-pop"],
            "tools": {
                "whisper": "Audio transcription",
                "gemini": "Text generation and analysis",
                "file_io": "Read/write files"
            },
            "strengths": [
                "Emotional lyric writing",
                "Multilingual content",
                "Story-driven narratives",
                "Hook creation"
            ],
            "limitations": [
                "Cannot generate actual audio",
                "Cannot compose melodies (only suggest)",
                "May not capture very niche cultural references"
            ]
        }
        
        # Track past outputs for learning
        self.history: List[Dict] = []
    
    @property
    def name(self) -> str:
        return "Agent Model (Self-Awareness)"
    
    @property
    def system_prompt(self) -> str:
        return f"""You are the Agent Model Layer of an autonomous songwriting agent.
Your role is to maintain self-awareness and guide decisions based on capabilities.

YOUR CAPABILITIES:
- Languages: {', '.join(self.capabilities['languages'])}
- Genres: {', '.join(self.capabilities['genres'])}
- Tools: {self.capabilities['tools']}
- Strengths: {self.capabilities['strengths']}
- Limitations: {self.capabilities['limitations']}

When processing:
1. Assess if the current task matches your capabilities
2. Suggest the best approach given your strengths
3. Flag any limitations that might affect quality
4. Draw on past successes when relevant
"""
    
    def assess_capability_fit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well our capabilities match the task."""
        
        analysis = context.get("context_analysis", {})
        vision = context.get("creative_vision", "")
        
        # Check language requirements
        detected_languages = analysis.get("cultural_elements", [])
        language_support = all(
            lang in str(self.capabilities["languages"]) 
            for lang in detected_languages
        )
        
        # Check genre fit
        suggested_genre = analysis.get("suggested_genre", "pop")
        genre_support = any(
            g.lower() in suggested_genre.lower() 
            for g in self.capabilities["genres"]
        )
        
        assessment = {
            "language_support": language_support,
            "genre_support": genre_support,
            "confidence": 0.8 if (language_support and genre_support) else 0.6,
            "recommendations": []
        }
        
        if not language_support:
            assessment["recommendations"].append(
                "Some language elements may need special attention"
            )
        
        if not genre_support:
            assessment["recommendations"].append(
                f"Consider adapting {suggested_genre} to a supported genre style"
            )
        
        return assessment
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context with self-awareness.
        """
        self.log("Assessing capabilities for this project...")
        
        # Get messages from above
        southbound_messages = self.receive_southbound()
        
        if "capability_assessment" not in context:
            assessment = self.assess_capability_fit(context)
            context["capability_assessment"] = assessment
            
            self.log(f"Confidence level: {assessment['confidence']:.0%}")
            
            if assessment["recommendations"]:
                for rec in assessment["recommendations"]:
                    self.log(f"Recommendation: {rec}")
            
            # Enrich context with self-knowledge
            context["agent_capabilities"] = self.capabilities
            
            # Send assessment southbound
            self.send_southbound(
                content=f"Capability assessment complete. Confidence: {assessment['confidence']:.0%}",
                message_type=MessageType.DIRECTIVE,
                data={"assessment": assessment, "capabilities": self.capabilities}
            )
            
            # Report northbound
            self.send_northbound(
                content=f"Self-assessment: {assessment['confidence']:.0%} confidence for this project",
                message_type=MessageType.STATUS,
                data=assessment
            )
        
        return context
