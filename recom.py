# =====================================================
# MindBridge - LLM Recommendation Module
# =====================================================
import json
import logging
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

log = logging.getLogger("recommendation")
MODELS = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-lite-latest"]
TIMEOUT_MS = 30000
MAX_TOKENS = 2048
RUN_FULL_TESTS = True 

class LLMOutput(BaseModel):
    summary: str
    recommendations: list[str]

SYSTEM_PROMPT = """You give general well-being guidance inside a student app.
The app shows a "Well-being Risk Indicator". It is NOT a diagnosis.

Boundaries:
- You are not a doctor, therapist, or healthcare professional. Never say or imply you are.
- Never diagnose or suggest the person has a mental-health condition.
- No medical claims, no medication advice, no promised outcomes.
- Use ONLY the factors provided. Do not invent others. Do not quote the risk score.
- Avoid alarming or dramatic language. Be warm, calm, and non-judgmental.

Personalization:
- Every recommendation must be practical and specific (what to do, how, roughly when)
  and clearly tied to one of the listed factors.
- Different factor combinations must produce clearly different advice.

Tone by risk level:
- Low: encouraging; reinforce healthy habits and prevention.
- Moderate: targeted, manageable changes; mention that talking to someone can help.
- High: gentle and simple steps; clearly encourage reaching out to someone they trust or a professional.

Output: "summary" = max 2 sentences. "recommendations" = exactly 3 items, 1-2 sentences each."""

DISCLAIMER = ("This is a Well-being Risk Indicator and general guidance, "
              "not a diagnosis or a substitute for professional advice.")
SUPPORT_MESSAGES = {
    "Low": "If things change or start to feel harder, support is available.",
    "Moderate": "Consider seeking professional support if you feel you need additional help.",
    "High": ("Consider reaching out to a professional or someone you trust soon. "
             "If you are in immediate danger, contact your local emergency services."),
}
SUPPORT_RESOURCES = [
    {"name": "A doctor, GP, or qualified mental-health professional", "url": None},
    {"name": "Your school, college, or workplace counselling service (if available)", "url": None},
    {"name": "Find A Helpline - verified helplines by country", "url": "https://findahelpline.com"},
    {"name": "WHO - mental health information", "url": "https://www.who.int/health-topics/mental-health"},
    {"name": "US only: 988 Suicide & Crisis Lifeline (call or text 988)", "url": "https://988lifeline.org"},
]
EMERGENCY_NOTE = "If you are in immediate danger, contact your local emergency services."

FALLBACK_TIPS = {
    "academic": "Break big tasks into small daily goals and schedule short breaks between study blocks.",
    "sleep": "Try a consistent bedtime and wake time, and avoid screens for 30 minutes before bed.",
    "financial": "Write down your monthly costs and look into budgeting or financial-aid support.",
    "satisfaction": "Note which parts of your studies feel draining and talk to a tutor or advisor about them.",
}
GENERIC_TIPS = ["Take short daily walks or breaks away from screens.",
                "Talk to a friend, family member, or mentor about how things are going."]
LOW_TIPS = ["Keep up your healthy routines, such as regular sleep, meals, and breaks.",
            "Check in with yourself weekly and reach out to someone if things change."]

def _fallback(level, factors):
    if level == "Low":
        tips = LOW_TIPS
    else:
        tips = [t for k, t in FALLBACK_TIPS.items() if any(k in f.lower() for f in factors)]
        tips = (tips + GENERIC_TIPS)[:4]
    return {"summary": "Personalized guidance is unavailable right now, so here are some general suggestions.",
            "recommendations": tips, "source": "fallback"}

def _clean_factors(factors):
    if not isinstance(factors, (list, tuple)):
        return []
    return [str(f).strip()[:80] for f in factors if str(f).strip()][:3]   # top 3

def _normalize_level(level):
    level = str(level).strip().capitalize()
    return level if level in SUPPORT_MESSAGES else "Moderate"

def _call_llm(prompt):
    client = genai.Client(http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    last_err = None
    for model in MODELS:
        for attempt in range(2):
            try:
                r = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=LLMOutput,
                        temperature=0.6, max_output_tokens=MAX_TOKENS))
                if r.parsed and r.parsed.recommendations:
                    return r.parsed
                last_err = ValueError("empty output")
                break
            except errors.ServerError as e:      # 503/504: retry once, then next model
                last_err = e
                time.sleep(2)
            except errors.ClientError as e:      # 404 / 429 / bad key: next model
                last_err = e
                break
    raise last_err or RuntimeError("all models failed")

def generate_recommendation(risk_score, risk_level, important_factors):
    """Never raises. Always returns a dict the frontend can render."""
    level = _normalize_level(risk_level)
    factors = _clean_factors(important_factors)
    try:
        score = max(0.0, min(1.0, float(risk_score)))
    except (TypeError, ValueError):
        score = None
    prompt = (f"Risk level: {level}\nRisk score (context only, do not quote): {score}\n"
              "Important factors:\n" + ("\n".join(f"- {f}" for f in factors) or "- (none identified)"))
    try:
        out = _call_llm(prompt)
        body = {"summary": out.summary, "recommendations": out.recommendations, "source": "ai"}
    except Exception as e:
        log.warning("LLM failed (%s): %s", type(e).__name__, str(e)[:200])
        body = _fallback(level, factors)
    return {**body, "risk_level": level,
            "professional_support": SUPPORT_MESSAGES[level],
            "disclaimer": DISCLAIMER,
            "support_resources": SUPPORT_RESOURCES,
            "emergency_note": EMERGENCY_NOTE}

