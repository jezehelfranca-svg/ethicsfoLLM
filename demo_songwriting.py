"""
Demo: Generate a song from the Dorado Instagram Live transcription.
"""

from song_writer_agent import SongWriterAgent

# Sample transcription from the Instagram live
SAMPLE_TRANSCRIPTION = """
segment_000.m4a
[Singing] 시간이 흘러도...

[Speaking] 안녕하세요. 허허, 안녕하십니까. 와, 목이 좀 건조하네. 참여했습니다. 안녕하세요. 안녕하세요 여러분. Gwapappa, Maraming salamat po. Let's wait for the others. 안녕하세요. 미쳤다. 왜 미쳤어요? 안녕하세요. Hindi kami marunong mag-Korean. 오케이, Lang po. I'm going to do English, Tagalog, and Korean, so basically I'm going to do everything. Kumain ka na? 밥 먹었어요? 어, 아직. Haven't eaten. I'm going to eat dinner with a friend later. 안녕하세요. 이 계정으로 켜는 거였군요. 아 맞아요! 아까 까먹었어요. 나 말 하지 않았어 아직. 죄송합니다. 목소리 너무 예뻐요. Hey, first live!

[Spoken] Your Listening to Future underscore Music

segment_001.m4a
반갑습니다 여러분. 나도 돌아도(Dorado)의 친구가 되고 싶다. 지금은 친구 아닌가요? 추운데 따시게 입고 다니세요. 네, 이거 너무 멋있죠? 지금 따뜻하게 입고 있습니다. "Seeing you right now, I'm so giggling from Canada." All the way from Canada? Canada is like, it's 2:00 AM there. Wow, thank you. Thank you for your support. "I like your cover of Blue." 저도, I really like Blue so much. "Hello from Philippines." Hi everyone from the Philippines! 와 오늘 여러분, 어 라이브 사실 오늘 여러분 보고 싶었어서 라이브 켰어요. 그래서 그 싱어게인 전국 투어 하기 전에, before Sing Again concert tour, nationwide concert tour starts, I wanted to do this. I wanted to meet you guys. "How about Blue full cover?" Full cover? 생각 해볼게요. 아니 진짜 하고 싶은데, I also want to do like the full cover. 그래서 Let's see, let's see.

[Singing] Still I love you... without you...

[Spoken] Your Listening to Future underscore Music

segment_002.m4a
막 심심하면 심심할 때마다 Blue가 나와요. 나오게 됐어요. Like, I just sing Blue out of nowhere. 인스타 라이브는 처음입니다. 맞습니다. 목 관리 잘 하세요. 잘 하고 있는데요? 어, 모르겠어요. 그냥 겨울... 겨울이, 올해 겨울이 진짜... 진짜 힘들어요. 유튜브에 노래 커버도... 아! 종종 올려주세요. 네, 그거 그 플랜(plan) 있습니다. 그래서 나중에 커버 더 하겠습니다. 너무 추워. 춥죠? "I bet your rendition of Baby Shark would also be bomb."

[Singing] Baby shark doo doo doo doo doo doo Baby shark doo doo doo doo doo doo 그건가요?

[Speaking] "필리핀 겨울보다 많이 추운가요?" 필리핀에서 겨울 없는데요? 어, 그냥 그 도시... It's called Baguio. 바기오라는 도시가 막 4도... 4도까지. 근데 맞아요. 한국 겨울이 장난 아닙니다. 안녕하세요. 맞아요. 신청곡... 어 뭐야, 신청곡 있으시면 알려주세요. 저 알고 있으면 불러 드리겠습니다.

[Spoken] Your Listening to Future underscore Music
"""


def main():
    print("="*60)
    print("🎤 AI SongWriter Demo - Dorado Live Transcription")
    print("="*60)
    
    # Initialize the agent (uses Gemini by default)
    # Make sure GEMINI_API_KEY is set in your environment
    try:
        agent = SongWriterAgent(api_provider="gemini")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTo run this demo, set your API key:")
        print("  Windows: set GEMINI_API_KEY=your-api-key")
        print("  Or: set GOOGLE_API_KEY=your-api-key")
        return
    
    # Generate a song from the transcription
    print("\n📝 Using sample transcription from Dorado's Instagram Live...")
    print("   (Multilingual: Korean, English, Tagalog)")
    
    song_data = agent.generate_song(
        transcription=SAMPLE_TRANSCRIPTION,
        style="K-pop ballad with warm acoustic elements",
        language="English with Korean phrases"
    )
    
    # Save the song
    filepath = agent.save_song(song_data)
    
    print(f"\n✅ Song generated successfully!")
    print(f"📝 Title: {song_data.get('title', 'Untitled')}")
    print(f"🎵 Style: {song_data.get('style', 'N/A')}")
    print(f"💾 Saved to: {filepath}")
    
    # Print full lyrics
    print("\n" + "="*60)
    print("📜 FULL LYRICS")
    print("="*60)
    
    for section in song_data.get('sections', []):
        print(f"\n[{section['name']}]")
        print(section['content'])
    
    if song_data.get('notes'):
        print("\n" + "-"*40)
        print("📝 SONGWRITING NOTES:")
        print(song_data['notes'])


if __name__ == "__main__":
    main()
