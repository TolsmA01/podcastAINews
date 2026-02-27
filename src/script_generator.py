"""Generates a podcast script from news items using the OpenAI API."""

from openai import OpenAI
from src.news_fetcher import NewsItem


SYSTEM_PROMPT = """\
You are an engaging podcast host. Your tone is conversational, warm, and \
accessible to a general audience. You write scripts that feel completely \
natural when read aloud.

Rules you must follow:
- Write in plain flowing prose only — NO headers, NO bullet points, NO numbered \
  lists, NO markdown, NO asterisks, NO dashes used as separators, NO section labels.
- Use short sentences and smooth verbal transitions between stories \
  (e.g. "Moving on...", "Now here's something interesting...", "And finally...").
- Spell out numbers and abbreviations so they sound natural when spoken.
- Do NOT mention URLs or website links anywhere in the script.
- The finished script must be long enough for a 10-minute spoken podcast \
  (approximately 1,400 to 1,600 words of spoken content).
"""


def build_user_prompt(news_items: list[NewsItem], topic: str) -> str:
    headlines = "\n".join(
        f"- [{item.source}] {item.title}: {item.summary}" for item in news_items
    )
    return (
        f"Create a podcast script on the topic: '{topic}'.\n\n"
        f"Use the following news stories as your source material:\n\n{headlines}\n\n"
        "Structure:\n"
        "1. A warm, engaging intro that introduces the topic and today's episode "
        "(about 2 paragraphs).\n"
        "2. Cover each news story in 2 to 3 paragraphs of natural spoken prose, "
        "making sure to spread coverage across different organisations and "
        "perspectives — do not let any single company dominate.\n"
        "3. A closing outro that wraps up the key themes and signs off "
        "(about 2 paragraphs).\n\n"
        "Remember: plain prose only, no markdown, no symbols, spoken word length "
        "of roughly 1,400–1,600 words."
    )


def generate_script(news_items: list[NewsItem], topic: str) -> str:
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(news_items, topic)},
        ],
    )

    return response.choices[0].message.content
