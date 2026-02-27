"""Converts the podcast script to audio using the OpenAI TTS API (voice: echo)."""

import io
import re
from pathlib import Path

from openai import OpenAI
from pydub import AudioSegment

# OpenAI TTS limit per request
_CHUNK_LIMIT = 4000


def _clean_for_speech(text: str) -> str:
    """Strip markdown, headers, bullets, and symbols that should not be spoken."""
    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold / italic markers
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}([^_\n]+)_{1,2}", r"\1", text)
    # Remove bullet / list markers
    text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown link syntax [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove leftover brackets
    text = re.sub(r"[\[\]]", "", text)
    # Remove remaining symbols: # * _ ` ~ | > ^
    text = re.sub(r"[#*_`~|>^]", "", text)
    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_into_chunks(text: str, max_chars: int = _CHUNK_LIMIT) -> list[str]:
    """Split text at sentence boundaries to stay within TTS character limits."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def generate_audio(script: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    cleaned = _clean_for_speech(script)
    chunks = _split_into_chunks(cleaned)

    print(f"[audio_generator] Generating audio in {len(chunks)} chunk(s)...")

    segments: list[AudioSegment] = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"[audio_generator] Processing chunk {i}/{len(chunks)}...")
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="echo",
            input=chunk,
        )
        audio_bytes = io.BytesIO(response.content)
        segments.append(AudioSegment.from_mp3(audio_bytes))

    combined = segments[0]
    for seg in segments[1:]:
        combined += seg

    combined.export(str(output_path), format="mp3")
    print(f"[audio_generator] Audio saved to {output_path}")
    return output_path
