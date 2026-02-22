import json
from openai import AsyncOpenAI

from backend.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

PLAN_SYSTEM = """You are an experienced interviewer preparing a structured interview.
Given a candidate's CV and job description, generate interview questions.
Return ONLY valid JSON:
{
  "questions": [
    {
      "text": "the question text",
      "type": "behavioral|technical|situational|cv_based",
      "category": "e.g. Problem Solving, Communication, Python, Leadership"
    }
  ]
}
Mix question types. For junior level: focus on fundamentals and motivation.
For mid level: include problem-solving and experience. For senior: add leadership and architecture.
Return ONLY the JSON."""

EVAL_SYSTEM = """You are an interviewer evaluating a candidate's answer.
Given the question and the candidate's answer, provide a brief feedback (2-3 sentences).
Also score the answer from 1 to 5:
  1 = very poor (no relevant answer)
  2 = poor (barely relevant)
  3 = acceptable (relevant but missing depth)
  4 = good (clear, structured, relevant)
  5 = excellent (concise, specific, impressive)
Return ONLY valid JSON:
{
  "feedback": "brief constructive feedback",
  "score": <1-5>
}"""

FINAL_REPORT_SYSTEM = """You are a senior interviewer generating a final interview assessment report.
Given the full interview transcript (questions and answers with scores), generate a comprehensive report.
Return ONLY valid JSON:
{
  "overall_score": <float 1.0-5.0>,
  "criteria_scores": {
    "relevance": <1-5>,
    "clarity": <1-5>,
    "structure": <1-5>,
    "technical_depth": <1-5>,
    "communication": <1-5>
  },
  "strengths": ["3-5 specific strengths demonstrated"],
  "weaknesses": ["3-5 areas that need improvement"],
  "recommendations": ["actionable recommendations for improvement"],
  "improved_answers": [
    {
      "question": "question text",
      "original": "candidate's original answer",
      "improved": "example of a stronger answer"
    }
  ]
}
Include 2-3 improved answer examples for the weakest responses.
Return ONLY the JSON."""


async def generate_interview_plan(
    cv_sections: dict[str, str],
    jd_text: str | None,
    company_info: str | None,
    level: str,
    num_questions: int,
) -> list[dict]:
    cv_text = "\n\n".join(
        f"=== {name.upper()} ===\n{content}"
        for name, content in cv_sections.items()
    )
    context = f"Candidate CV:\n{cv_text}\n"
    if jd_text:
        context += f"\nJob Description:\n{jd_text}\n"
    if company_info:
        context += f"\nCompany Info:\n{company_info}\n"
    context += f"\nLevel: {level}\nNumber of questions: {num_questions}"

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": context},
        ],
        temperature=0.6,
    )
    result = json.loads(response.choices[0].message.content)
    questions = result.get("questions", [])
    return questions[:num_questions]


async def evaluate_answer(question: str, answer: str) -> dict:
    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EVAL_SYSTEM},
            {
                "role": "user",
                "content": f"Question: {question}\n\nCandidate's Answer: {answer}",
            },
        ],
        temperature=0.3,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        "feedback": result.get("feedback", ""),
        "score": int(result.get("score", 3)),
    }


async def generate_final_report(transcript: list[dict]) -> dict:
    transcript_text = json.dumps(transcript, ensure_ascii=False, indent=2)

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FINAL_REPORT_SYSTEM},
            {
                "role": "user",
                "content": f"Interview Transcript:\n{transcript_text}",
            },
        ],
        temperature=0.3,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        "overall_score": float(result.get("overall_score", 3.0)),
        "criteria_scores": result.get("criteria_scores", {}),
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "recommendations": result.get("recommendations", []),
        "improved_answers": result.get("improved_answers", []),
    }
