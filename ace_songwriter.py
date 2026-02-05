"""
ACE Songwriter - Autonomous Cognitive Songwriting Agent
========================================================
A multi-agent system that writes songs based on transcriptions or circumstances.

Integrates three Dave Shap frameworks:
- ACE (Autonomous Cognitive Entities) - 6-layer cognitive architecture
- GATO (Global Alignment Taxonomy Omnibus) - Heuristic Imperatives
- HAAS (Hierarchical Autonomous Agent Swarm) - Dynamic sub-agents & oversight

Usage:
    python ace_songwriter.py --input transcription.txt
    python ace_songwriter.py --circumstance "A farewell to winter"
    python ace_songwriter.py --input transcription.txt --verbose --oversight
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ace_framework import (
    ACEAgent, NorthboundBus, SouthboundBus, LayerID
)
from layers import (
    AspirationalLayer,
    GlobalStrategyLayer,
    AgentModelLayer,
    ExecutiveFunctionLayer,
    CognitiveControlLayer,
    TaskProsecutionLayer
)
from agent_spawner import AgentSpawner, spawn_songwriter_agent
from oversight_board import SupremeOversightBoard, create_songwriter_sob, Verdict

# Try to import Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class ACESongwriter(ACEAgent):
    """
    The main autonomous songwriting agent.
    
    Integrates:
    - 6 ACE cognitive layers
    - GATO Heuristic Imperatives (in Aspirational Layer)
    - HAAS Agent Swarm patterns (dynamic sub-agents, oversight board)
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 verbose: bool = False, 
                 output_dir: str = None,
                 enable_oversight: bool = False,
                 enable_spawner: bool = False):
        super().__init__(api_key=api_key, verbose=verbose, output_dir=output_dir)
        
        # Agent Swarm components
        self.agent_spawner = AgentSpawner(llm_model=self.llm, verbose=verbose) if enable_spawner else None
        self.oversight_board = create_songwriter_sob(llm_model=self.llm, verbose=verbose) if enable_oversight else None
        
        # Initialize all 6 cognitive layers
        self._setup_layers()
    
    def _setup_layers(self):
        """Initialize and register all cognitive layers."""
        
        # Layer 1: Aspirational (The Soul)
        self.register_layer(AspirationalLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose
        ))
        
        # Layer 2: Global Strategy (The Visionary)
        self.register_layer(GlobalStrategyLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose
        ))
        
        # Layer 3: Agent Model (Self-Awareness)
        self.register_layer(AgentModelLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose
        ))
        
        # Layer 4: Executive Function (The Producer)
        self.register_layer(ExecutiveFunctionLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose
        ))
        
        # Layer 5: Cognitive Control (The Director)
        self.register_layer(CognitiveControlLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose
        ))
        
        # Layer 6: Task Prosecution (The Writers)
        self.register_layer(TaskProsecutionLayer(
            northbound_bus=self.northbound,
            southbound_bus=self.southbound,
            llm_model=self.llm,
            verbose=self.verbose,
            output_dir=str(self.output_dir)
        ))
    
    def write_song(self, 
                   transcription: str = None,
                   circumstance: str = None,
                   max_cycles: int = 15) -> dict:
        """
        Write a song based on transcription or circumstance.
        
        Args:
            transcription: Text transcription to base the song on
            circumstance: Description of circumstances/theme
            max_cycles: Maximum cognitive cycles
            
        Returns:
            Final context with the generated song
        """
        input_data = {
            "transcription": transcription,
            "circumstance": circumstance,
            "description": f"Write a song based on: {(transcription or circumstance or 'general theme')[:100]}..."
        }
        
        print("\n" + "="*60)
        print("🎵 ACE SONGWRITING AGENT")
        print("="*60)
        print(f"\n📚 Input: {input_data['description']}")
        print(f"🧠 Layers: {len(self.layers)} cognitive layers active")
        if self.oversight_board:
            print(f"⚖️ Supreme Oversight Board: ACTIVE (3 personas)")
        if self.agent_spawner:
            print(f"🔧 Agent Spawner: ACTIVE")
        print(f"🔄 Max cycles: {max_cycles}")
        print("\n" + "-"*60)
        
        result = self.run(input_data, max_cycles=max_cycles)
        
        # If oversight is enabled, run SOB review on the final song
        if self.oversight_board and result.get("song_parts"):
            print("\n⚖️ Running Supreme Oversight Board review...")
            song_content = "\n\n".join([
                f"{k.upper()}:\n{v}" for k, v in result["song_parts"].items()
            ])
            review = self.oversight_board.review(
                song_content, 
                context=result.get("context_analysis", {})
            )
            result["sob_review"] = review
            print(f"\n⚖️ SOB Verdict: {review['overall_verdict'].value.upper()}")
            print(f"   ({review['approved_count']}/{review['total_personas']} personas approved)")
        
        print("\n" + "-"*60)
        
        if result.get("status") == "complete":
            print("✅ Song generation complete!")
            if result.get("output_file"):
                print(f"📄 Output: {result['output_file']}")
        else:
            print(f"⚠️ Status: {result.get('status', 'unknown')}")
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description="ACE Songwriter - Autonomous Cognitive Songwriting Agent"
    )
    parser.add_argument('--input', '-i', type=str, 
                       help='Path to transcription file')
    parser.add_argument('--circumstance', '-c', type=str,
                       help='Circumstance/theme description for the song')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output (show layer activity)')
    parser.add_argument('--oversight', action='store_true',
                       help='Enable Supreme Oversight Board (SOB) review')
    parser.add_argument('--spawner', action='store_true',
                       help='Enable dynamic sub-agent spawning')
    parser.add_argument('--max-cycles', '-m', type=int, default=15,
                       help='Maximum cognitive cycles (default: 15)')
    parser.add_argument('--output-dir', '-o', type=str,
                       help='Output directory for generated songs')
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: No API key found!")
        print("\nPlease set your Gemini API key:")
        print("  Windows PowerShell: $env:GEMINI_API_KEY = 'your-key'")
        print("  Windows CMD: set GEMINI_API_KEY=your-key")
        print("\nGet a free API key at: https://aistudio.google.com/")
        return
    
    if not HAS_GEMINI:
        print("❌ Error: google-generativeai package not installed!")
        print("\nInstall with: pip install google-generativeai")
        return
    
    # Get input
    transcription = None
    circumstance = args.circumstance
    
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ Error: File not found: {args.input}")
            return
        with open(input_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
        print(f"📖 Loaded transcription from: {input_path.name}")
    
    if not transcription and not circumstance:
        print("❌ Error: Please provide --input or --circumstance")
        print("\nExamples:")
        print("  python ace_songwriter.py --input transcription.txt")
        print("  python ace_songwriter.py --circumstance 'A love song about winter'")
        return
    
    # Create and run agent
    agent = ACESongwriter(
        api_key=api_key,
        verbose=args.verbose,
        output_dir=args.output_dir,
        enable_oversight=args.oversight,
        enable_spawner=args.spawner
    )
    
    result = agent.write_song(
        transcription=transcription,
        circumstance=circumstance,
        max_cycles=args.max_cycles
    )
    
    # Print song preview if available
    if result.get("song_parts"):
        parts = result["song_parts"]
        print("\n" + "="*60)
        print("🎤 SONG PREVIEW")
        print("="*60)
        
        if "hook" in parts:
            print("\n[CHORUS]")
            # Show first few lines
            lines = parts["hook"].split('\n')[:6]
            for line in lines:
                if line.strip() and not line.startswith('[') and not line.startswith('TITLE'):
                    print(f"  {line}")
        
        if "verse1" in parts:
            print("\n[VERSE 1]")
            lines = parts["verse1"].split('\n')[:4]
            for line in lines:
                if line.strip() and not line.startswith('['):
                    print(f"  {line}")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    main()
