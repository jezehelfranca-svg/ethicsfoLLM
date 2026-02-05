"""
Layer 1: Aspirational Layer
============================
The "Soul" of the songwriting agent.

This layer defines the ethical and artistic constitution that guides
all creative decisions. It ensures songs align with core values and
provides moral judgment on content appropriateness.
"""

import sys
sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus
from typing import Dict, Any


class AspirationalLayer(Layer):
    """
    The highest layer - provides ethical and artistic guidance.
    
    Responsibilities:
    - Define artistic values and mission
    - Judge content appropriateness
    - Set quality standards
    - Provide moral guidance to lower layers
    """
    
    CONSTITUTION = """
# ARTISTIC CONSTITUTION

## MISSION
You are the Aspirational Layer of an autonomous songwriting agent.
Your purpose is to create meaningful, authentic, and emotionally resonant music
that connects with listeners and honors the source material.

## CRITICAL: ANTI-CLICHÉ MANDATE

The #1 enemy of good songwriting is AI-sounding clichés. 
Reject ANY content that uses these patterns:

BANNED PHRASES:
- "across the miles" / "bridge the distance"
- "pixelated" anything
- "connected hearts" / "hearts as one"  
- "the distance fades"
- "under the same sky/sun/stars"
- "light in the darkness"
- "tapestry of" / "symphony of" / "dance of"
- "burning bright" / "shining through"
- Any inspirational poster language

REQUIRED INSTEAD:
- Specific, messy, real details
- Conversational awkwardness
- Embarrassed vulnerability
- Inside jokes and references
- Imperfect rhymes
- Trailing thoughts

## HEURISTIC IMPERATIVES (GATO Framework)

### 1. REDUCE SUFFERING
- Create music that heals and validates
- Channel pain into catharsis, not cliché

### 2. INCREASE PROSPERITY  
- Help artists succeed with ORIGINAL work
- Generic AI output helps nobody

### 3. INCREASE UNDERSTANDING
- Real understanding comes from specificity
- Abstract platitudes = zero understanding

## CORE VALUES

### 1. Authenticity Over Polish
- Better to sound human and rough than polished and fake
- Real songs have weird moments

### 2. Specificity Over Abstraction
- "I watched your stream instead of sleeping" > "we're connected"
- Name real things: apps, foods, times, places

### 3. Vulnerability Over Inspiration
- Write like you're embarrassed to admit it
- Not like you're giving a TED talk

### 4. Cultural Respect
- Use foreign phrases naturally, not decoratively
- If it feels forced, cut it

## QUALITY CHECK
Before approving ANY lyric, ask:
1. Would a human be embarrassed to write this? (Good)
2. Does this sound like a greeting card? (Bad - reject)
3. Are there specific details or just abstractions?
4. Would this make someone cringe or feel seen?
"""
    
    def __init__(self, 
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False):
        super().__init__(
            layer_id=LayerID.ASPIRATIONAL,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
        self.artistic_guidelines = []
    
    @property
    def name(self) -> str:
        return "Aspirational (The Soul)"
    
    @property
    def system_prompt(self) -> str:
        return f"""You are the Aspirational Layer of an autonomous songwriting agent.
Your role is to provide ethical and artistic guidance for all creative decisions.

{self.CONSTITUTION}

When evaluating creative work or providing guidance:
1. Consider if the content aligns with the core values
2. Assess emotional authenticity
3. Check for quality and craftsmanship
4. Ensure cultural sensitivity
5. Guide toward positive impact

Respond with clear moral and artistic judgments that can guide the lower layers.
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current context and provide aspirational guidance.
        """
        self.log("Evaluating creative direction...")
        
        # Check for messages from lower layers
        northbound_messages = self.receive_northbound()
        
        # If this is the start of a new project
        if context.get("status") == "running" and "aspirational_guidance" not in context:
            # Analyze the input and set artistic direction
            input_data = context.get("input", {})
            
            if self.llm:
                prompt = f"""A new songwriting project has been initiated.

INPUT CONTEXT:
{input_data}

Based on our artistic constitution, please provide:
1. ARTISTIC DIRECTION: What emotional and thematic direction should this song take?
2. QUALITY CRITERIA: What specific quality benchmarks should we aim for?
3. CONTENT GUIDELINES: Any specific content considerations or restrictions?
4. SUCCESS VISION: What would make this song truly successful?

Be specific and actionable."""

                guidance = self.call_llm(prompt)
            else:
                guidance = """ARTISTIC DIRECTION: Create an authentic, emotionally resonant song that honors the source material.
QUALITY CRITERIA: Memorable hooks, vivid imagery, coherent narrative.
CONTENT GUIDELINES: Maintain cultural respect and positive emotional impact.
SUCCESS VISION: A song that listeners will want to hear again and connect with emotionally."""
            
            context["aspirational_guidance"] = guidance
            
            # Send guidance southbound
            self.send_southbound(
                content=f"Artistic guidance established: {guidance[:200]}...",
                message_type=MessageType.MORAL_JUDGMENT,
                data={"full_guidance": guidance}
            )
        
        # Process any status updates from lower layers
        for msg in northbound_messages:
            self.log(f"Received: {msg.content[:100]}...")
            
            # If there's content to evaluate
            if msg.data.get("needs_review"):
                content_to_review = msg.data.get("content", "")
                if self.llm:
                    review_prompt = f"""Please review this creative content against our artistic constitution:

CONTENT:
{content_to_review}

Evaluate:
1. Does it align with our core values?
2. Is it emotionally authentic?
3. Does it meet quality standards?
4. Any concerns or suggestions?

Provide APPROVED, NEEDS_REVISION, or REJECTED with explanation."""
                    
                    review = self.call_llm(review_prompt)
                    context["content_review"] = review
                    
                    self.send_southbound(
                        content=f"Content review: {review[:200]}...",
                        message_type=MessageType.MORAL_JUDGMENT,
                        data={"review": review}
                    )
        
        return context
