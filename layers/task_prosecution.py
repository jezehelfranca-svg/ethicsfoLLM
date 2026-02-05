"""
Layer 6: Task Prosecution Layer
================================
The "Writers" of the songwriting agent.

This layer executes the actual creative work - analyzing transcriptions,
writing lyrics, structuring songs, and producing output.
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append('..')

from ace_framework import Layer, LayerID, MessageType, NorthboundBus, SouthboundBus


class TaskProsecutionLayer(Layer):
    """
    Executes the actual songwriting tasks.
    
    Responsibilities:
    - Analyze transcriptions
    - Write lyrics (verses, chorus, bridge)
    - Structure songs
    - Save output files
    """
    
    def __init__(self,
                 northbound_bus: NorthboundBus,
                 southbound_bus: SouthboundBus,
                 llm_model=None,
                 verbose: bool = False,
                 output_dir: str = None):
        super().__init__(
            layer_id=LayerID.TASK_PROSECUTION,
            northbound_bus=northbound_bus,
            southbound_bus=southbound_bus,
            llm_model=llm_model,
            verbose=verbose
        )
        
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "generated_songs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Song components being built
        self.song_parts: Dict[str, str] = {}
        self.song_metadata: Dict[str, str] = {}
    
    @property
    def name(self) -> str:
        return "Task Prosecution (The Writers)"
    
    @property
    def system_prompt(self) -> str:
        return """You are a HUMAN songwriter, not an AI. Write like a real person.

## CRITICAL: AVOID THESE AI CLICHÉS AT ALL COSTS

BANNED PHRASES (never use):
- "across the miles" / "bridge the distance"
- "pixelated" anything
- "connected hearts" / "hearts as one"
- "the distance fades"
- "under the same sky/sun/stars"
- "light in the darkness"
- "echoes through"
- "tapestry of"
- "journey of"
- "dance of"
- "symphony of"
- "waves of emotion"
- "burning bright"
- "rising as one"
- "breaking through"
- Any phrase that sounds like an inspirational poster

## HOW TO WRITE LIKE A HUMAN

1. BE SPECIFIC, NOT ABSTRACT
   ❌ "We're connected across the world"
   ✅ "Your 3AM is my lunch break, but we're both here"

2. USE REAL, MESSY DETAILS
   ❌ "Sharing moments together"  
   ✅ "You spilled coffee on your keyboard, we all screamed"

3. WRITE CONVERSATIONALLY
   ❌ "Our hearts unite in harmony"
   ✅ "I don't even know your real name but I'd fight for you"

4. EMBRACE IMPERFECTION
   - Real songs have awkward rhymes sometimes
   - Real songs trail off or repeat weirdly
   - Real songs reference specific inside jokes

5. BE VULNERABLE, NOT POETIC
   ❌ "Love flows like a river eternal"
   ✅ "I watched your stream instead of sleeping again"

6. AVOID SYMMETRY
   - Not every line needs to rhyme perfectly
   - Vary line lengths
   - Let thoughts run into each other

## YOUR VOICE
Write like:
- The tired fan at 4am who can't stop watching
- Someone texting their friend about why they're crying over a stranger
- A person who feels slightly embarrassed about how much they care

NOT like:
- An inspirational speaker
- A greeting card
- A motivational poster
- Corporate marketing copy
"""
    
    def execute_analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the analysis task."""
        input_data = context.get("input", {})
        transcription = input_data.get("transcription", "")
        circumstance = input_data.get("circumstance", "")
        
        if not self.llm:
            return {
                "themes": ["connection", "warmth"],
                "emotions": ["joy", "gratitude"],
                "key_phrases": [],
                "analysis_complete": True
            }
        
        prompt = f"""Deeply analyze this source material for songwriting:

SOURCE:
{transcription or circumstance}

Provide a comprehensive analysis:
1. EMOTIONAL LANDSCAPE: What emotions are present? What's the emotional journey?
2. KEY THEMES: What are the main themes we should capture?
3. MEMORABLE MOMENTS: What specific phrases or moments stand out?
4. NARRATIVE THREAD: What story could we tell?
5. UNIQUE ELEMENTS: What makes this special (multilingual, cultural, personal)?
6. SONG POTENTIAL: What type of song would best capture this?

Be specific and draw direct connections to potential lyrics."""

        analysis = self.call_llm(prompt)
        return {"deep_analysis": analysis, "analysis_complete": True}
    
    def execute_structure(self, context: Dict[str, Any]) -> str:
        """Define the song structure."""
        vision = context.get("creative_vision", "")
        analysis = context.get("context_analysis", {})
        
        if not self.llm:
            return "INTRO - VERSE1 - PRECHORUS - CHORUS - VERSE2 - PRECHORUS - CHORUS - BRIDGE - FINAL CHORUS - OUTRO"
        
        prompt = f"""Based on the creative vision, define the optimal song structure:

CREATIVE VISION:
{vision}

ANALYSIS:
{json.dumps(analysis, indent=2) if isinstance(analysis, dict) else analysis}

Return:
1. STRUCTURE: The section order (e.g., INTRO - VERSE1 - CHORUS...)
2. RATIONALE: Why this structure serves the emotional arc
3. SECTION NOTES: Brief notes for each section's purpose

Be specific about how the structure serves the story."""

        return self.call_llm(prompt)
    
    def execute_hook(self, context: Dict[str, Any]) -> str:
        """Write the main hook/chorus."""
        vision = context.get("creative_vision", "")
        analysis = context.get("context_analysis", {})
        
        if not self.llm:
            return """[CHORUS]
We're speaking different tongues
But singing the same song tonight
Across the cold, across the miles
Your warmth becomes my light"""
        
        prompt = f"""Write the CHORUS - the emotional heart of the song.

CREATIVE VISION:
{vision}

THEMES: {analysis.get('themes', ['connection'])}
MOOD: {analysis.get('mood', 'uplifting')}

Create a chorus that:
1. Is immediately memorable and singable
2. Captures the core emotional truth
3. Has a strong hook/title phrase
4. Can work as a standalone emotional statement
5. Uses vivid imagery

Format:
[CHORUS]
(4-8 lines of lyrics)

Also suggest:
- TITLE: A song title based on your chorus
- MELODY NOTES: Suggestions for melody/delivery"""

        return self.call_llm(prompt)
    
    def execute_verse(self, verse_num: int, context: Dict[str, Any]) -> str:
        """Write a verse."""
        vision = context.get("creative_vision", "")
        chorus = self.song_parts.get("hook", "")
        prev_verse = self.song_parts.get(f"verse{verse_num-1}", "") if verse_num > 1 else ""
        
        if not self.llm:
            if verse_num == 1:
                return """[VERSE 1]
2 AM in Canada, you're still awake
Across the frozen miles between us
겨울이 추워도 (Even when winter's cold)
Your messages light up my screen"""
            else:
                return """[VERSE 2]
First live, first time, feeling so alive
Speaking every language of the heart
From Philippines to Seoul tonight
We're writing our story in the stars"""
        
        verse_context = "Set up the story" if verse_num == 1 else "Develop the narrative and add depth"
        
        prompt = f"""Write VERSE {verse_num} of the song.

PURPOSE: {verse_context}

CREATIVE VISION:
{vision}

CHORUS (for reference):
{chorus}

{"VERSE 1 (already written):" if verse_num > 1 else ""}
{prev_verse if verse_num > 1 else ""}

Create Verse {verse_num} that:
1. {"Introduces the story and hook the listener" if verse_num == 1 else "Builds on Verse 1 with new perspective or development"}
2. Uses concrete, specific imagery
3. Flows naturally into the pre-chorus/chorus
4. Has the right syllable count for singing
5. Maintains the established mood

Format:
[VERSE {verse_num}]
(4-8 lines of lyrics)"""

        return self.call_llm(prompt)
    
    def execute_bridge(self, context: Dict[str, Any]) -> str:
        """Write the bridge."""
        vision = context.get("creative_vision", "")
        verses = f"VERSE 1:\n{self.song_parts.get('verse1', '')}\n\nVERSE 2:\n{self.song_parts.get('verse2', '')}"
        chorus = self.song_parts.get("hook", "")
        
        if not self.llm:
            return """[BRIDGE]
So when the distance feels too far
Remember we share the same sky, same stars
언젠가 만나게 될 거야 (Someday we'll meet)
Until then, I'll keep singing for you"""
        
        prompt = f"""Write the BRIDGE - the emotional pivot of the song.

CREATIVE VISION:
{vision}

CURRENT SONG:
{verses}

CHORUS:
{chorus}

Create a bridge that:
1. Provides contrast (musically/lyrically different)
2. Offers a new perspective or revelation
3. Builds to the final chorus
4. Is the emotional climax
5. Can include multilingual elements if appropriate

Format:
[BRIDGE]
(4-6 lines of lyrics)"""

        return self.call_llm(prompt)
    
    def execute_prechorus(self, context: Dict[str, Any]) -> str:
        """Write the pre-chorus."""
        chorus = self.song_parts.get("hook", "")
        
        if not self.llm:
            return """[PRE-CHORUS]
And even though the world keeps spinning
Even though we're oceans apart
I feel you here"""
        
        prompt = f"""Write the PRE-CHORUS - builds anticipation for the chorus.

CHORUS (target):
{chorus}

Create a pre-chorus that:
1. Builds tension and anticipation
2. Lifts energy toward the chorus
3. Is shorter than verses (2-4 lines)
4. Creates a natural transition

Format:
[PRE-CHORUS]
(2-4 lines of lyrics)"""

        return self.call_llm(prompt)
    
    def execute_polish(self, context: Dict[str, Any]) -> str:
        """Polish and refine all sections."""
        all_parts = "\n\n".join([
            f"{k.upper()}:\n{v}" for k, v in self.song_parts.items()
        ])
        
        if not self.llm:
            return "Song polished and ready."
        
        prompt = f"""Review and polish the complete song:

CURRENT LYRICS:
{all_parts}

Review for:
1. FLOW: Do sections transition smoothly?
2. CONSISTENCY: Is the voice/perspective consistent?
3. WORD CHOICE: Are there any weak words to strengthen?
4. IMAGERY: Are metaphors effective and coherent?
5. SINGABILITY: Do the syllables flow for singing?

Provide:
1. Any suggested changes (specify section and line)
2. Overall assessment
3. Final polished version if changes are needed"""

        return self.call_llm(prompt)
    
    def execute_finalize(self, context: Dict[str, Any]) -> Path:
        """Compile and save the final song."""
        analysis = context.get("context_analysis", {})
        
        # Extract title from hook if available
        hook = self.song_parts.get("hook", "")
        title_match = re.search(r'TITLE:\s*(.+)', hook)
        title = title_match.group(1).strip() if title_match else "Untitled Song"
        
        # Clean title for filename
        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.md"
        filepath = self.output_dir / filename
        
        # Compile song
        md_content = f"""# {title}

**Generated by ACE Songwriting Agent**  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Song Details

| Property | Value |
|----------|-------|
| Genre | {analysis.get('suggested_genre', 'Pop')} |
| Mood | {analysis.get('mood', 'Uplifting')} |
| Themes | {', '.join(analysis.get('themes', ['connection'])[:3])} |

---

## Lyrics

"""
        # Add sections in order
        section_order = ["verse1", "prechorus", "hook", "verse2", "prechorus", "hook", "bridge", "hook"]
        section_names = {
            "verse1": "VERSE 1",
            "verse2": "VERSE 2", 
            "prechorus": "PRE-CHORUS",
            "hook": "CHORUS",
            "bridge": "BRIDGE"
        }
        
        for section in section_order:
            if section in self.song_parts:
                content = self.song_parts[section]
                # Clean up any existing headers in content
                cleaned = re.sub(r'\[(VERSE|CHORUS|PRE-CHORUS|BRIDGE).*?\]', '', content).strip()
                md_content += f"### [{section_names.get(section, section.upper())}]\n\n{cleaned}\n\n"
        
        md_content += """---

## About This Song

This song was autonomously generated by the ACE (Autonomous Cognitive Entities) 
Songwriting Agent, which uses a 6-layer cognitive architecture to think, 
decide, and create.
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        self.log(f"Song saved to: {filepath}")
        return filepath
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute songwriting tasks.
        """
        self.log("Executing creative work...")
        
        # Get current task from context (set by Executive Function)
        current_task = context.get("current_task")
        
        if not current_task:
            self.log("No current task")
            return context
        
        task_id = current_task.get("id")
        
        # Skip if we already completed this task
        if context.get("last_executed_task") == task_id:
            return context
        
        self.log(f"Executing task: {task_id}")
        
        result = None
        
        try:
            if task_id == "analyze":
                result = self.execute_analyze(context)
                context.update(result)
                
            elif task_id == "structure":
                result = self.execute_structure(context)
                self.song_parts["structure"] = result
                
            elif task_id == "hook":
                result = self.execute_hook(context)
                self.song_parts["hook"] = result
                
            elif task_id == "verse1":
                result = self.execute_verse(1, context)
                self.song_parts["verse1"] = result
                
            elif task_id == "verse2":
                result = self.execute_verse(2, context)
                self.song_parts["verse2"] = result
                
            elif task_id == "bridge":
                result = self.execute_bridge(context)
                self.song_parts["bridge"] = result
                
            elif task_id == "prechorus":
                result = self.execute_prechorus(context)
                self.song_parts["prechorus"] = result
                
            elif task_id == "polish":
                result = self.execute_polish(context)
                self.song_parts["polish_notes"] = result
                
            elif task_id == "finalize":
                filepath = self.execute_finalize(context)
                result = str(filepath)
                context["output_file"] = result
            
            # Signal completion via context (for Executive Function to pick up)
            context["last_completed_task_id"] = task_id
            context["last_task_output"] = result
            context["last_executed_task"] = task_id
            context["current_task"] = None  # Clear current task
            
            self.log(f"Task '{task_id}' completed!")
            
            # Store current song state
            context["song_parts"] = self.song_parts
            
        except Exception as e:
            self.log(f"Task failed: {e}")
            import traceback
            traceback.print_exc()
            context["status"] = "error"
            context["error"] = str(e)
        
        return context
