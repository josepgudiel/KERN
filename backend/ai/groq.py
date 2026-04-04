"""All Groq API calls — extracted from app.py. Model: llama-3.3-70b-versatile."""
from __future__ import annotations

import hashlib
import logging
import os
import time

import pandas as pd

try:
    from groq import Groq as _GroqClient
    _GROQ_AVAILABLE = True
except Exception:
    _GroqClient = None
    _GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)


def _get_groq_client():
    """Returns a configured Groq client or None if unavailable."""
    if not _GROQ_AVAILABLE:
        return None
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        return _GroqClient(api_key=api_key)
    except Exception:
        return None


def _groq_generate(client, prompt, retries=1):
    """Call Groq with automatic retry on rate limit (429)."""
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = []
        for m in prompt:
            role = "assistant" if m.get("role") == "model" else m.get("role", "user")
            parts = m.get("parts", [m.get("content", "")])
            content = parts[0] if isinstance(parts, list) else parts
            messages.append({"role": role, "content": content})

    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.4,
                max_tokens=1000,
            )
            if not resp.choices:
                class _Empty:
                    text = ""
                return _Empty()
            msg = resp.choices[0].message
            raw_text = getattr(msg, "content", None) or ""
            class _Resp:
                text = raw_text
            return _Resp()
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                logger.warning("Groq rate limit hit — retrying in 5 seconds...")
                time.sleep(5)
                continue
            raise


def _generate_health_brief(df: pd.DataFrame, product_clusters, currency: str = "$", business_profile: dict | None = None) -> dict | None:
    """Generate a 2-paragraph health brief via AI."""
    if len(df) < 30:
        return None

    client = _get_groq_client()
    if client is None:
        return None

    from .prompts import _build_data_context, _build_profile_context

    data_ctx = _build_data_context(df, product_clusters, currency=currency)
    profile_ctx = _build_profile_context(business_profile)
    profile_context_block = (
        f"\nBUSINESS PROFILE (use this to tune language and benchmarks):\n{profile_ctx}"
        if profile_ctx else ""
    )

    prompt = (
        "You are a business advisor writing a 2-paragraph health brief for a small "
        "business owner. They will read this the moment their data loads.\n\n"
        "Write exactly 2 paragraphs. No headers. No bullet points. No markdown. "
        "Plain prose only. Maximum 120 words total.\n\n"
        "Paragraph 1 — State of the business right now:\n"
        "Open with the single most important fact (revenue total, trend direction, or a "
        "standout product). Name actual numbers. Be direct — no preamble like \"based on "
        "your data.\" Just state it. End with a one-sentence read on whether the business "
        "is in a good position, needs attention, or is at a turning point.\n\n"
        "Paragraph 2 — The one thing to focus on this week:\n"
        "Name a specific product or time pattern from the data. Give one concrete action "
        "tied to a number. This should feel like advice from someone who has run a "
        "business, not a report generator.\n\n"
        "Rules:\n"
        "- Never use: \"leverage\", \"actionable\", \"insights\", \"it's worth noting\", "
        "\"the data suggests\", \"notably\", \"in conclusion\"\n"
        "- Every sentence must contain at least one number or product name from the data\n"
        "- If profit or margin figures appear in the data, they are estimates — say "
        "\"estimated profit\" not \"profit\", and never imply the margin is exact\n"
        "- If industry/goal is known from the business profile, use industry-appropriate "
        "language (e.g. \"covers\" for restaurants, \"footfall\" for retail)\n"
        "- 120 words maximum — enforced, not a guideline\n"
        f"{profile_context_block}\n\n"
        f"BUSINESS DATA:\n{data_ctx}"
    )

    try:
        response = _groq_generate(client, prompt)
        full_text = (response.text or "").strip()
        parts = full_text.split("\n\n", 1)
        if len(parts) == 2:
            result = {"paragraph_1": parts[0].strip(), "paragraph_2": parts[1].strip()}
        else:
            result = {"paragraph_1": full_text, "paragraph_2": ""}
        return result
    except Exception:
        return None


def _generate_narrative_report(df: pd.DataFrame, product_clusters, period_label: str | None = None, currency: str = "$", business_profile: dict | None = None) -> str | None:
    """Generate a 3-paragraph plain-English business performance summary via AI."""
    client = _get_groq_client()
    if client is None:
        return None

    from .prompts import _build_data_context, _build_profile_context
    from engine.insights import _derive_period_label

    if period_label is None:
        period_label = _derive_period_label(df)
    data_context = _build_data_context(df, product_clusters, currency=currency)
    profile_ctx = _build_profile_context(business_profile)
    profile_block = f"\n\n{profile_ctx}\n" if profile_ctx else ""
    prompt = f"""You are writing a brief business performance summary for a small business owner. \
They will forward this to their accountant, business partner, or investor.

Write exactly 3 paragraphs. No headers, no bullet points, no markdown. \
Plain prose only. Each paragraph should be 3–5 sentences.

Paragraph 1 — Performance overview:
Summarize overall revenue, order volume, and trend direction for {period_label}. \
Mention the top-performing product by name and its revenue. \
If week-over-week or period-over-period data is available, include the direction.
Be specific with numbers. Do not use vague language.

Paragraph 2 — What's working and what needs attention:
Name the 1–2 strongest products and why they matter (volume, margin, or growth). \
Name 1 product that is underperforming or declining, if one exists.
If a pricing or bundle opportunity exists, mention it in one sentence.
Be specific. Use the actual product names and dollar figures from the data.

Paragraph 3 — Forward-looking action:
Give 2 concrete actions the owner should take in the next 30 days.
Each action should reference a specific product or time pattern from the data.
End with one sentence that frames the overall business health in plain English.
No filler. No "in conclusion." Just useful guidance.

Rules:
- Never use the words: "leverage", "synergy", "actionable", "insights", "data-driven", \
  "it's worth noting", "notably", "the data suggests", "it appears"
- Write like a trusted advisor who has run a business — direct, warm, specific
- If cost/margin data is available, mention profit, not just revenue
- If profit figures are marked as estimated in the data, say "estimated profit" — \
  never present an estimated margin as a known fact
- Maximum 200 words total
{profile_block}
BUSINESS DATA:
{data_context}"""
    try:
        response = _groq_generate(client, prompt)
        return response.text.strip() if response and response.text else None
    except Exception:
        return None


def generate_advisor_reply(
    df: pd.DataFrame,
    product_clusters,
    message: str,
    conversation_history: list | None = None,
    business_profile: dict | None = None,
    currency: str = "$",
) -> str:
    """Generate an AI advisor reply using Groq."""
    client = _get_groq_client()
    if client is None:
        return "AI advisor is not available — please set your GROQ_API_KEY."

    from .prompts import build_data_summary, build_advisor_system_prompt, _build_data_context

    data_summary = build_data_summary(df, currency=currency)
    rich_context = _build_data_context(df, product_clusters, currency=currency)
    system_msg = build_advisor_system_prompt(data_summary, profile=business_profile, rich_context=rich_context)

    messages = [{"role": "system", "content": system_msg}]
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": message})

    try:
        response = _groq_generate(client, messages)
        return response.text.strip() if response and response.text else "I couldn't generate a response. Please try again."
    except Exception as e:
        return f"AI advisor encountered an error: {str(e)}"
