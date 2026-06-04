import os
import tempfile
from pathlib import Path


def record_audio(duration: int = 5, output: str = "input.wav") -> str:
    try:
        import sounddevice as sd
        import soundfile as sf

        fs = 16000
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        sf.write(output, recording, fs)
        return f"Recorded {duration}s audio to {output}"
    except ImportError:
        return "Error: sounddevice not installed (pip install sounddevice)"
    except Exception as e:
        return f"Error recording audio: {e}"


def transcribe(audio_path: str) -> str:
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"].strip()
    except ImportError:
        return "Error: openai-whisper not installed (pip install openai-whisper)"
    except Exception as e:
        return f"Error transcribing audio: {e}"


def speak(text: str, lang: str = "ru") -> str:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return "Spoken via pyttsx3"
    except ImportError:
        pass
    except Exception as e:
        return f"Error with pyttsx3: {e}"

    try:
        from gtts import gTTS
        import pygame

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts = gTTS(text=text, lang=lang)
            tts.save(f.name)
            tmp_path = f.name

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.unlink(tmp_path)
        return "Spoken via gTTS"
    except ImportError:
        pass
    except Exception as e:
        return f"Error with gTTS: {e}"

    try:
        import edge_tts
        import asyncio

        async def _speak():
            tts = edge_tts.Communicate(text, voice="ru-RU-DariyaNeural")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                await tts.save(f.name)
                tmp_path = f.name
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.unlink(tmp_path)

        asyncio.run(_speak())
        return "Spoken via edge-tts"
    except ImportError:
        return "Error: no TTS library available (try: pip install pyttsx3 gtts edge-tts)"
    except Exception as e:
        return f"Error with edge-tts: {e}"


def voice_chat(lm, memory) -> None:
    print("Voice chat started. Press Ctrl+C to stop.")
    try:
        while True:
            result = record_audio()
            print(result)
            if result.startswith("Error"):
                break

            text = transcribe("input.wav")
            print(f"You: {text}")
            if text.startswith("Error"):
                continue

            response = lm.chat(text, memory)
            print(f"AI: {response}")
            speak(response)
    except KeyboardInterrupt:
        print("\nVoice chat ended.")
    except Exception as e:
        print(f"Voice chat error: {e}")
