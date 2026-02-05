"""
AI Songwriting Agent
=====================
Generates song lyrics based on transcriptions or given circumstances.
Uses OpenAI GPT or Google Gemini API for intelligent lyric generation.

Usage:
    python song_writer_agent.py --input transcription.txt
    python song_writer_agent.py --circumstance "A farewell to winter, meeting fans for the first time"
    python song_writer_agent.py --interactive
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# Try to import API libraries
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class SongWriterAgent:
    """AI Agent that writes songs based on transcriptions or circumstances."""
    
    def __init__(self, api_provider="gemini", api_key=None):
        """
        Initialize the SongWriter Agent.
        
        Args:
            api_provider: "gemini" or "openai"
            api_key: API key (or set via environment variable)
        """
        self.api_provider = api_provider.lower()
        self.output_dir = Path(__file__).parent / "generated_songs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize API
        if self.api_provider == "gemini":
            if not HAS_GEMINI:
                raise ImportError("Please install google-generativeai: pip install google-generativeai")
            api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        elif self.api_provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("Please install openai: pip install openai")
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Please set OPENAI_API_KEY environment variable")
            self.client = openai.OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")
    
    def analyze_transcription(self, transcription: str) -> dict:
        """
        Analyze a transcription to extract themes, emotions, and key elements.
        
        Args:
            transcription: The raw transcription text
            
        Returns:
            Dictionary with extracted elements
        """
        analysis_prompt = f"""Analyze this transcription and extract songwriting elements.
The transcription may be multilingual (Korean, English, Tagalog, etc.).

TRANSCRIPTION:
{transcription}

Extract and return a JSON object with:
{{
    "main_themes": ["list of main themes/topics discussed"],
    "emotions": ["list of emotions present (joy, nostalgia, warmth, excitement, etc.)"],
    "key_phrases": ["memorable or poetic phrases that could inspire lyrics"],
    "context": "brief description of the situation/event",
    "mood": "overall mood (upbeat, melancholic, hopeful, etc.)",
    "languages_present": ["languages detected"],
    "potential_song_styles": ["suggested genre/style for the song"],
    "character_insights": "insights about the speaker's personality/character"
}}

Return ONLY the JSON object, no other text."""

        response = self._call_api(analysis_prompt)
        
        # Parse JSON from response
        try:
            # Clean up response to extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback if parsing fails
        return {
            "main_themes": ["connection", "warmth", "music"],
            "emotions": ["joy", "gratitude"],
            "key_phrases": [],
            "context": "Live interaction with fans",
            "mood": "upbeat",
            "languages_present": ["mixed"],
            "potential_song_styles": ["pop", "ballad"],
            "character_insights": "Warm and engaging personality"
        }
    
    def generate_song(self, 
                      transcription: str = None, 
                      circumstance: str = None,
                      style: str = None,
                      language: str = "English",
                      song_structure: str = "verse-chorus-verse-chorus-bridge-chorus") -> dict:
        """
        Generate a song based on transcription or circumstance.
        
        Args:
            transcription: Transcription text to base the song on
            circumstance: Description of circumstances/theme for the song
            style: Musical style (pop, ballad, rock, etc.)
            language: Language for the lyrics
            song_structure: Structure of the song
            
        Returns:
            Dictionary with song details
        """
        # Analyze transcription if provided
        analysis = None
        if transcription:
            print("📖 Analyzing transcription...")
            analysis = self.analyze_transcription(transcription)
            print(f"   Found themes: {', '.join(analysis.get('main_themes', []))}")
            print(f"   Detected mood: {analysis.get('mood', 'N/A')}")
        
        # Build the song generation prompt
        context_section = ""
        if analysis:
            context_section = f"""
ANALYSIS OF SOURCE MATERIAL:
- Main Themes: {', '.join(analysis.get('main_themes', []))}
- Emotions: {', '.join(analysis.get('emotions', []))}
- Key Phrases: {', '.join(analysis.get('key_phrases', []))}
- Context: {analysis.get('context', '')}
- Mood: {analysis.get('mood', '')}
- Character: {analysis.get('character_insights', '')}
"""
        
        if circumstance:
            context_section += f"\nCIRCUMSTANCE/THEME:\n{circumstance}\n"
        
        style_hint = style if style else (analysis.get('potential_song_styles', ['pop'])[0] if analysis else 'pop')
        
        song_prompt = f"""You are a professional songwriter. Write a complete, original song based on the following context.

{context_section}

SONG REQUIREMENTS:
- Style/Genre: {style_hint}
- Language: {language}
- Structure: {song_structure}
- Make it emotionally resonant and authentic
- Include vivid imagery and metaphors
- Each verse should tell part of the story
- The chorus should be catchy and memorable
- If the source is multilingual, you may incorporate phrases from other languages

Return the song in this exact format:
---
TITLE: [Song Title]
STYLE: [Musical Style]
TEMPO: [BPM suggestion]
KEY: [Suggested key]
MOOD: [Overall mood]

[INTRO]
(instrumental notes if any)

[VERSE 1]
(lyrics here)

[PRE-CHORUS]
(lyrics here)

[CHORUS]
(lyrics here)

[VERSE 2]
(lyrics here)

[CHORUS]
(lyrics here)

[BRIDGE]
(lyrics here)

[FINAL CHORUS]
(lyrics here)

[OUTRO]
(lyrics or instrumental notes)
---

SONGWRITING NOTES:
(Brief notes about the song's meaning and vocal delivery suggestions)
"""

        print("🎵 Generating song...")
        song_text = self._call_api(song_prompt)
        
        # Parse the song
        song_data = self._parse_song(song_text)
        song_data['source_analysis'] = analysis
        song_data['raw_output'] = song_text
        
        return song_data
    
    def _parse_song(self, song_text: str) -> dict:
        """Parse the generated song text into structured data."""
        result = {
            'title': 'Untitled',
            'style': 'Unknown',
            'tempo': 'Unknown',
            'key': 'Unknown',
            'mood': 'Unknown',
            'sections': [],
            'notes': ''
        }
        
        # Extract metadata
        title_match = re.search(r'TITLE:\s*(.+)', song_text)
        if title_match:
            result['title'] = title_match.group(1).strip()
        
        style_match = re.search(r'STYLE:\s*(.+)', song_text)
        if style_match:
            result['style'] = style_match.group(1).strip()
            
        tempo_match = re.search(r'TEMPO:\s*(.+)', song_text)
        if tempo_match:
            result['tempo'] = tempo_match.group(1).strip()
            
        key_match = re.search(r'KEY:\s*(.+)', song_text)
        if key_match:
            result['key'] = key_match.group(1).strip()
            
        mood_match = re.search(r'MOOD:\s*(.+)', song_text)
        if mood_match:
            result['mood'] = mood_match.group(1).strip()
        
        # Extract sections
        section_pattern = r'\[([A-Z\s\d]+)\]\n(.*?)(?=\[|SONGWRITING NOTES:|$)'
        sections = re.findall(section_pattern, song_text, re.DOTALL | re.IGNORECASE)
        for section_name, content in sections:
            result['sections'].append({
                'name': section_name.strip(),
                'content': content.strip()
            })
        
        # Extract notes
        notes_match = re.search(r'SONGWRITING NOTES:\s*(.*?)(?:---|$)', song_text, re.DOTALL)
        if notes_match:
            result['notes'] = notes_match.group(1).strip()
        
        return result
    
    def _call_api(self, prompt: str) -> str:
        """Call the configured API with the given prompt."""
        if self.api_provider == "gemini":
            response = self.model.generate_content(prompt)
            return response.text
        elif self.api_provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional songwriter with expertise in multiple genres and languages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            return response.choices[0].message.content
    
    def save_song(self, song_data: dict, filename: str = None) -> Path:
        """Save the generated song to a file."""
        if not filename:
            safe_title = re.sub(r'[^\w\s-]', '', song_data.get('title', 'Untitled'))
            safe_title = safe_title.replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_title}_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        # Create markdown content
        md_content = f"""# {song_data.get('title', 'Untitled')}

**Generated by AI SongWriter Agent**  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Song Details

| Property | Value |
|----------|-------|
| Style | {song_data.get('style', 'N/A')} |
| Tempo | {song_data.get('tempo', 'N/A')} |
| Key | {song_data.get('key', 'N/A')} |
| Mood | {song_data.get('mood', 'N/A')} |

---

## Lyrics

"""
        for section in song_data.get('sections', []):
            md_content += f"### [{section['name']}]\n\n{section['content']}\n\n"
        
        if song_data.get('notes'):
            md_content += f"""---

## Songwriting Notes

{song_data['notes']}
"""
        
        if song_data.get('source_analysis'):
            analysis = song_data['source_analysis']
            md_content += f"""
---

## Source Analysis

- **Main Themes:** {', '.join(analysis.get('main_themes', []))}
- **Emotions:** {', '.join(analysis.get('emotions', []))}
- **Mood:** {analysis.get('mood', 'N/A')}
- **Context:** {analysis.get('context', 'N/A')}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return filepath
    
    def interactive_mode(self):
        """Run the agent in interactive mode."""
        print("\n" + "="*60)
        print("🎤 AI SONGWRITING AGENT - Interactive Mode")
        print("="*60)
        print("\nI'll help you write songs based on transcriptions or circumstances.\n")
        
        while True:
            print("\nOptions:")
            print("1. Generate song from transcription file")
            print("2. Generate song from pasted text")
            print("3. Generate song from circumstance/theme")
            print("4. Quit")
            
            choice = input("\nChoice (1-4): ").strip()
            
            if choice == "1":
                filepath = input("Enter path to transcription file: ").strip()
                if Path(filepath).exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        transcription = f.read()
                    self._generate_and_save(transcription=transcription)
                else:
                    print("❌ File not found!")
                    
            elif choice == "2":
                print("Paste your transcription (enter 'END' on a new line when done):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == 'END':
                        break
                    lines.append(line)
                transcription = '\n'.join(lines)
                if transcription.strip():
                    self._generate_and_save(transcription=transcription)
                else:
                    print("❌ No text provided!")
                    
            elif choice == "3":
                circumstance = input("Describe the circumstance/theme for the song: ").strip()
                if circumstance:
                    style = input("Musical style (leave blank for auto): ").strip() or None
                    language = input("Language (default: English): ").strip() or "English"
                    self._generate_and_save(circumstance=circumstance, style=style, language=language)
                else:
                    print("❌ No circumstance provided!")
                    
            elif choice == "4":
                print("\n🎵 Thanks for using AI SongWriter Agent! Keep creating! 🎵\n")
                break
            else:
                print("Invalid choice, please try again.")
    
    def _generate_and_save(self, **kwargs):
        """Generate a song and save it."""
        try:
            song_data = self.generate_song(**kwargs)
            filepath = self.save_song(song_data)
            
            print(f"\n✅ Song generated successfully!")
            print(f"📝 Title: {song_data.get('title', 'Untitled')}")
            print(f"🎵 Style: {song_data.get('style', 'N/A')}")
            print(f"💾 Saved to: {filepath}")
            
            # Print preview
            print("\n" + "-"*40)
            print("PREVIEW:")
            print("-"*40)
            for section in song_data.get('sections', [])[:3]:
                print(f"\n[{section['name']}]")
                lines = section['content'].split('\n')[:4]
                print('\n'.join(lines))
                if len(section['content'].split('\n')) > 4:
                    print("...")
            print("-"*40)
            
        except Exception as e:
            print(f"\n❌ Error generating song: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Songwriting Agent - Generate songs from transcriptions or circumstances"
    )
    parser.add_argument('--input', '-i', type=str, help='Path to transcription file')
    parser.add_argument('--circumstance', '-c', type=str, help='Circumstance/theme for the song')
    parser.add_argument('--style', '-s', type=str, help='Musical style (pop, ballad, rock, etc.)')
    parser.add_argument('--language', '-l', type=str, default='English', help='Language for lyrics')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--api', type=str, default='gemini', choices=['gemini', 'openai'],
                       help='API provider to use (default: gemini)')
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    
    args = parser.parse_args()
    
    # Initialize agent
    try:
        agent = SongWriterAgent(api_provider=args.api)
    except (ImportError, ValueError) as e:
        print(f"❌ Error initializing agent: {e}")
        print("\nMake sure you have:")
        print("  1. Installed the required package:")
        print("     - For Gemini: pip install google-generativeai")
        print("     - For OpenAI: pip install openai")
        print("  2. Set the appropriate API key environment variable:")
        print("     - For Gemini: GEMINI_API_KEY or GOOGLE_API_KEY")
        print("     - For OpenAI: OPENAI_API_KEY")
        return
    
    if args.interactive:
        agent.interactive_mode()
    elif args.input:
        # Read transcription file
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ File not found: {args.input}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
        
        song_data = agent.generate_song(
            transcription=transcription,
            style=args.style,
            language=args.language
        )
        filepath = agent.save_song(song_data, args.output)
        print(f"\n✅ Song saved to: {filepath}")
        
    elif args.circumstance:
        song_data = agent.generate_song(
            circumstance=args.circumstance,
            style=args.style,
            language=args.language
        )
        filepath = agent.save_song(song_data, args.output)
        print(f"\n✅ Song saved to: {filepath}")
        
    else:
        # No arguments - run interactive
        agent.interactive_mode()


if __name__ == "__main__":
    main()
