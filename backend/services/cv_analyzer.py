import json
from openai import AsyncOpenAI

from backend.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are an expert career coach and CV reviewer.
Analyze the given CV and return ONLY valid JSON with this exact structure:
{
  "issues": ["list of specific problems found in the CV"],
  "tips": ["list of actionable improvement tips"],
  "rewrites": [
    {"original": "original weak phrase", "improved": "improved version"}
  ]
}

Focus on:
- Missing sections (contacts, summary, skills, experience, education)
- Weak action verbs ("responsible for", "worked on", "helped with")
- Lack of metrics and quantifiable achievements
- Vague descriptions without specifics
- Overly long paragraphs instead of bullet points
- Missing dates, company names, or job titles
- Repetitive language

Provide at least 5 issues and 5 tips. Return ONLY the JSON, no extra text."""


async def analyze_cv(cv_sections: dict[str, str]) -> dict:
    sections_text = "\n\n".join(
        f"=== {name.upper()} ===\n{content}"
        for name, content in cv_sections.items()
    )
    user_message = f"Please analyze this CV:\n\n{sections_text}"

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "issues": result.get("issues", []),
        "tips": result.get("tips", []),
        "rewrites": result.get("rewrites", []),
    }
