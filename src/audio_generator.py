"""Converts the podcast script to an audio file using gTTS."""

from pathlib import Path
from gtts import gTTS


def generate_audio(script: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tts = gTTS(text=script, lang="en", slow=False)
    tts.save(str(output_path))

    print(f"[audio_generator] Audio saved to {output_path}")
    return output_path
