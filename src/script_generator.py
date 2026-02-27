"""Generates a podcast script from news items using the OpenAI API."""

from openai import OpenAI
from src.news_fetcher import NewsItem

# Speaking-pace constants
_WORDS_PER_MINUTE = 130
_TARGET_MINUTES = 10
_TARGET_WORDS = _WORDS_PER_MINUTE * _TARGET_MINUTES   # 1300
_MIN_WORDS = _WORDS_PER_MINUTE * 9                    # 1170  (9 min threshold)
_MAX_EXPAND_ATTEMPTS = 3


SYSTEM_PROMPT = """\
You are an engaging podcast host. Your tone is conversational, warm, and \
accessible to a general audience. You write scripts that feel completely \
natural when read aloud.

Rules you must follow:
- Write in plain flowing prose only — NO headers, NO bullet points, NO numbered \
  lists, NO markdown, NO asterisks, NO dashes used as separators, NO section labels.
- Use short sentences and smooth verbal transitions between stories \
  (e.g. "Moving on...", "Now here is something interesting...", "And finally...").
- Spell out numbers and abbreviations so they sound natural when spoken.
- Do NOT mention URLs or website links anywhere in the script.
- LENGTH IS CRITICAL: the script must contain at least 1,300 words of spoken \
  content so that the audio runs for a full 10 minutes at a normal speaking pace. \
  This is a hard requirement — do not stop writing until you reach that length.
"""


def _word_count(text: str) -> int:
    return len(text.split())


def _estimate_minutes(text: str) -> float:
    return _word_count(text) / _WORDS_PER_MINUTE


def _initial_prompt(news_items: list[NewsItem], topic: str) -> str:
    headlines = "\n".join(
        f"- [{item.source}] {item.title}: {item.summary}" for item in news_items
    )
    return (
        f"Create a podcast script on the topic: '{topic}'.\n\n"
        f"Use the following news stories as your source material:\n\n{headlines}\n\n"
        "Structure:\n"
        "1. A warm, engaging intro that introduces the topic (2-3 paragraphs).\n"
        "2. Cover each news story in 3 to 4 paragraphs of natural spoken prose. "
        "Spread coverage across different organisations and perspectives — "
        "do not let any single company dominate.\n"
        "3. A closing outro that wraps up key themes and signs off (2-3 paragraphs).\n\n"
        f"IMPORTANT: The final script must be at least {_TARGET_WORDS} words long "
        f"(about {_TARGET_MINUTES} minutes of speech at a normal pace). "
        "Plain prose only — no markdown, no symbols."
    )


def _expand_prompt(current_script: str, topic: str, current_words: int) -> str:
    deficit = _TARGET_WORDS - current_words
    return (
        f"The podcast script below on '{topic}' is only {current_words} words "
        f"(about {current_words // _WORDS_PER_MINUTE} minutes). "
        f"It must be at least {_TARGET_WORDS} words for a 10-minute podcast. "
        f"Expand it by adding roughly {deficit} more words.\n\n"
        "Instructions:\n"
        "- Deepen the analysis and context for each story (add examples, implications, "
        "background, expert perspectives).\n"
        "- Add smooth verbal transitions and conversational asides.\n"
        "- Keep the same intro/outro structure.\n"
        "- Plain prose only — no markdown, no symbols, no headers.\n\n"
        "Return the FULL expanded script (not just the additions).\n\n"
        f"Current script:\n{current_script}"
    )


def generate_script(news_items: list[NewsItem], topic: str) -> str:
    client = OpenAI()

    # Initial generation
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _initial_prompt(news_items, topic)},
        ],
    )
    script = response.choices[0].message.content

    words = _word_count(script)
    mins = _estimate_minutes(script)
    print(f"[script_generator] Initial draft: {words} words (~{mins:.1f} min)")

    # Expand until we hit the target or exhaust attempts
    for attempt in range(1, _MAX_EXPAND_ATTEMPTS + 1):
        if words >= _MIN_WORDS:
            break

        print(
            f"[script_generator] Too short ({mins:.1f} min). "
            f"Expanding... (attempt {attempt}/{_MAX_EXPAND_ATTEMPTS})"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _expand_prompt(script, topic, words)},
            ],
        )
        script = response.choices[0].message.content
        words = _word_count(script)
        mins = _estimate_minutes(script)
        print(f"[script_generator] After expansion {attempt}: {words} words (~{mins:.1f} min)")

    print(f"[script_generator] Final script: {words} words (~{mins:.1f} min)")
    return script
