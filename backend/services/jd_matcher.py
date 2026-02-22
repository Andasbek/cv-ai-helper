import json
from openai import AsyncOpenAI

from backend.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

EXTRACT_SYSTEM = """You are a job requirements analyst.
Extract the key requirements from the given job description and return ONLY valid JSON:
{
  "hard_skills": ["specific technical skills, tools, languages, frameworks"],
  "soft_skills": ["interpersonal and soft skills"],
  "responsibilities": ["main job responsibilities"],
  "keywords": ["important keywords for ATS matching"]
}
Return ONLY the JSON, no extra text."""

MATCH_SYSTEM = """You are a career advisor comparing a candidate's CV to a job description.
Given the CV sections and JD requirements, return ONLY valid JSON:
{
  "match_score": <integer 0-100>,
  "matched_skills": ["skills present in both CV and JD"],
  "missing_skills": ["skills required by JD but missing from CV"],
  "recommendations": ["specific actionable recommendations to improve the CV for this role"]
}
Be accurate: match_score should reflect true overlap. Return ONLY the JSON."""


async def extract_jd_requirements(jd_text: str) -> dict:
    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"Job Description:\n\n{jd_text}"},
        ],
        temperature=0.2,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        "hard_skills": result.get("hard_skills", []),
        "soft_skills": result.get("soft_skills", []),
        "responsibilities": result.get("responsibilities", []),
        "keywords": result.get("keywords", []),
    }


async def match_cv_to_jd(cv_sections: dict[str, str], jd_requirements: dict) -> dict:
    cv_text = "\n\n".join(
        f"=== {name.upper()} ===\n{content}"
        for name, content in cv_sections.items()
    )
    jd_text = json.dumps(jd_requirements, indent=2)

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MATCH_SYSTEM},
            {
                "role": "user",
                "content": f"CV:\n{cv_text}\n\nJD Requirements:\n{jd_text}",
            },
        ],
        temperature=0.2,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        "match_score": int(result.get("match_score", 0)),
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "recommendations": result.get("recommendations", []),
    }
