"""Generates a podcast script from news items using the OpenAI API."""

from openai import OpenAI
from src.news_fetcher import NewsItem


SYSTEM_PROMPT = """\
You are an engaging podcast host for a daily AI news digest. Your tone is \
conversational, enthusiastic, and accessible to a general audience. Write \
scripts that feel natural when read aloud — use short sentences, smooth \
transitions, and avoid jargon.
"""


def build_user_prompt(news_items: list[NewsItem], podcast_name: str) -> str:
    headlines = "\n".join(
        f"- [{item.source}] {item.title}: {item.summary}" for item in news_items
    )
    return (
        f"Create a podcast script for '{podcast_name}'. "
        f"Cover the following news stories:\n\n{headlines}\n\n"
        "Include a brief intro, cover each story (1-2 paragraphs each), "
        "and end with a short outro. Use natural speech patterns."
    )


def generate_script(news_items: list[NewsItem], podcast_name: str = "AI News Daily") -> str:
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(news_items, podcast_name)},
        ],
    )

    return response.choices[0].message.content
