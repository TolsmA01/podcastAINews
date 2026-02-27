"""Entry point for podcastAINews."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.news_fetcher import fetch_news
from src.script_generator import generate_script
from src.audio_generator import generate_audio


def main() -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file or environment."
        )

    print("Fetching latest news...")
    news_items = fetch_news()

    if not news_items:
        print("No news items found. Check your config/config.yaml RSS feeds.")
        return

    print(f"Fetched {len(news_items)} news items. Generating podcast script...")
    script = generate_script(news_items)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_dir = Path("output")
    script_path = output_dir / f"podcast_{timestamp}.txt"
    audio_path = output_dir / f"podcast_{timestamp}.mp3"

    output_dir.mkdir(exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    print(f"Script saved to {script_path}")

    print("Generating audio...")
    generate_audio(script, audio_path)
    print("Done!")


if __name__ == "__main__":
    main()
