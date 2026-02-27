"""Entry point for podcastAINews."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.news_fetcher import fetch_news
from src.script_generator import generate_script, _estimate_minutes, _word_count
from src.audio_generator import generate_audio


def _prompt_topic() -> str:
    print("\n=== Podcast Generator ===")
    print("What topic should today's podcast cover?")
    print("Examples: 'artificial intelligence', 'climate tech', 'space exploration'")
    topic = input("Topic: ").strip()
    if not topic:
        topic = "technology"
        print(f"No topic entered — defaulting to '{topic}'.")
    return topic


def _format_sources(news_items) -> str:
    lines = ["Sources", "-------"]
    for item in news_items:
        lines.append(f"- [{item.source}] {item.title}")
        if item.link:
            lines.append(f"  {item.link}")
    return "\n".join(lines)


def main() -> None:
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to your .env file or environment."
        )

    topic = _prompt_topic()

    print(f"\nFetching news articles on '{topic}'...")
    news_items = fetch_news(topic)

    if not news_items:
        print("No news items found. Check your config/config.yaml RSS feeds.")
        return

    print(f"Fetched {len(news_items)} articles from {len({i.source for i in news_items})} sources.")
    print("Generating podcast script (~10 minutes)...")
    script = generate_script(news_items, topic)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    words = _word_count(script)
    mins = _estimate_minutes(script)
    print(f"Script: {words} words (~{mins:.1f} min estimated audio)")

    # Save script + sources to txt
    script_path = output_dir / f"podcast_{timestamp}.txt"
    sources_block = _format_sources(news_items)
    script_path.write_text(script + "\n\n" + sources_block, encoding="utf-8")
    print(f"Script saved to {script_path}")

    # Generate audio (sources are not read aloud)
    audio_path = output_dir / f"podcast_{timestamp}.mp3"
    print("Generating audio with OpenAI TTS (voice: echo)...")
    generate_audio(script, audio_path)

    print(f"\nDone! Files saved to {output_dir}/")
    print(f"  Script : {script_path.name}  ({words} words, ~{mins:.1f} min)")
    print(f"  Audio  : {audio_path.name}")


if __name__ == "__main__":
    main()
