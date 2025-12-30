import edge_tts
import asyncio
import os, time
import uuid
import sounddevice as sd
import soundfile as sf
async def generate_tts(text, voice, filename):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(filename)
    print(f"Saved TTS to {filename}")


def speak_text(text):
    print("MESSAGE TO SPEAK",text)
    voice = "fr-FR-DeniseNeural"
    filename = f"tmp_{uuid.uuid4()}.mp3"
    asyncio.run(generate_tts(text, voice, filename))

    # Wait briefly if file not yet fully written
    for _ in range(10):
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            break
        time.sleep(0.1)

    data,fs = sf.read(filename, dtype='float32')
    sd.play(data,fs)
    sd.wait()
    return filename
# Example use:
#asyncio.run(generate_tts("Hello Jean, welcome to your StaRL training platform!", voice="en-US-AriaNeural",filename="output.mp3"))
