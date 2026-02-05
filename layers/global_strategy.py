"""
Layer 2: Global Strategy Layer
===============================
The "Visionary" of the songwriting agent.

This layer analyzes the environmental context and sets the high-level
creative vision for the song project.
"""

import sys
sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus
from typing import Dict, Any
import json
import re


class GlobalStrategyLayer(Layer):
    """
    Sets high-level creative strategy based on context.
    
    Responsibilities:
    - Analyze source material (transcription themes, emotions)
    - Determine appropriate genre and style
    - Set target mood and audience
    - Create overall creative vision
    """
    
    def __init__(self,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False):
        super().__init__(
            layer_id=LayerID.GLOBAL_STRATEGY,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
    
    @property
    def name(self) -> str:
        return "Global Strategy (The Visionary)"
    
    @property
    def system_prompt(self) -> str:
        return """You are the Global Strategy Layer of an autonomous songwriting agent.
Your role is to analyze context and set the high-level creative vision.

CRITICAL: Your vision must ACTIVELY FIGHT against AI clichés.

When setting creative direction:

AVOID setting up for these AI patterns:
- Generic "connection/unity" themes → Instead: specific, awkward moments of connection
- "Light/darkness" metaphors → Instead: real objects, apps, times of day
- Universal inspiration → Instead: embarrassingly specific personal moments
- Polished emotional arcs → Instead: messy, trailing, human feelings

GUIDE TOWARD:
- Songs that sound like 4AM texts, not greeting cards
- Details the writer would be embarrassed to share
- Conversational tone over poetic flourishes
- Imperfect structures that feel real

Your vision should push the writers to be:
- Specific (name apps, foods, times, inside jokes)
- Vulnerable (admit the embarrassing parts)
- Conversational (like texting a friend, not writing poetry)
- Imperfect (don't force rhymes, let thoughts trail off)

Think like an indie producer who hates overproduced AI pop.
Be bold. Be weird. Be human.
"""
    
    def analyze_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the input context to extract creative elements."""
        
        transcription = input_data.get("transcription", "")
        circumstance = input_data.get("circumstance", "")
        
        if not self.llm:
            # Basic fallback analysis
            return {
                "themes": ["connection", "music", "emotion"],
                "emotions": ["warmth", "joy"],
                "suggested_genre": "pop ballad",
                "mood": "uplifting",
                "key_elements": []
            }
        
        prompt = f"""Analyze this context for songwriting:

TRANSCRIPTION/CIRCUMSTANCE:
{transcription or circumstance}

Extract and return a JSON object with:
{{
    "themes": ["main themes identified"],
    "emotions": ["emotions present"],
    "suggested_genre": "recommended genre/style",
    "mood": "overall mood",
    "tempo_feel": "slow/medium/upbeat",
    "key_phrases": ["memorable phrases that could inspire lyrics"],
    "cultural_elements": ["any cultural/language elements to honor"],
    "narrative_arc": "suggested story/emotional journey",
    "unique_angle": "what makes this special"
}}

Return ONLY the JSON object."""

        response = self.call_llm(prompt)
        
        # Parse JSON from response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return {
            "themes": ["connection"],
            "emotions": ["warmth"],
            "suggested_genre": "pop",
            "mood": "uplifting"
        }
    
    def create_creative_vision(self, 
                               analysis: Dict[str, Any],
                               aspirational_guidance: str) -> str:
        """Create a comprehensive creative vision for the song."""
        
        if not self.llm:
            return f"""CREATIVE VISION:
Genre: {analysis.get('suggested_genre', 'Pop')}
Mood: {analysis.get('mood', 'Uplifting')}
Themes: {', '.join(analysis.get('themes', ['connection']))}
The song should capture the emotional essence of the source material
while creating something fresh and memorable."""
        
        prompt = f"""Based on this analysis and aspirational guidance, create a comprehensive creative vision:

ANALYSIS:
{json.dumps(analysis, indent=2)}

ASPIRATIONAL GUIDANCE:
{aspirational_guidance}

Create a CREATIVE VISION document that includes:
1. SONG CONCEPT: One-paragraph description of what this song is about
2. GENRE & STYLE: Specific genre, influences, sonic palette
3. EMOTIONAL JOURNEY: How the song should make listeners feel
4. STRUCTURE RECOMMENDATION: Suggested song structure
5. KEY HOOKS: Ideas for memorable chorus/hooks
6. CULTURAL INTEGRATION: How to honor any multilingual/multicultural elements
7. UNIQUE SELLING POINT: What makes this song special

Be specific and inspiring. This vision will guide all creative decisions."""

        return self.call_llm(prompt)
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and set creative strategy.
        """
        self.log("Developing creative strategy...")
        
        # Get southbound messages (from Aspirational layer)
        southbound_messages = self.receive_southbound()
        aspirational_guidance = context.get("aspirational_guidance", "")
        
        for msg in southbound_messages:
            if msg.data.get("full_guidance"):
                aspirational_guidance = msg.data["full_guidance"]
        
        # If we haven't done analysis yet
        if "context_analysis" not in context:
            input_data = context.get("input", {})
            
            self.log("Analyzing input context...")
            analysis = self.analyze_context(input_data)
            context["context_analysis"] = analysis
            
            self.log("Creating creative vision...")
            vision = self.create_creative_vision(analysis, aspirational_guidance)
            context["creative_vision"] = vision
            
            # Send strategy southbound
            self.send_southbound(
                content=f"Creative vision established. Genre: {analysis.get('suggested_genre', 'undefined')}",
                message_type=MessageType.OBJECTIVE,
                data={
                    "analysis": analysis,
                    "vision": vision
                }
            )
            
            # Report status northbound
            self.send_northbound(
                content=f"Strategy defined: {analysis.get('suggested_genre', 'pop')} song about {', '.join(analysis.get('themes', ['connection'])[:2])}",
                message_type=MessageType.STATUS
            )
        
        return context
