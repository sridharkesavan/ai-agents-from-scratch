import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()
llm = anthropic.Anthropic()

def judge_report(topic: str, criteria: list, report: str) -> dict:
    criteria_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(criteria))

    judge_prompt = f"""You are a strict evaluator grading a research report against specific criteria.

Topic the report was written on: {topic}

Report to evaluate:
{report}

Criteria to check (grade each one independently):
{criteria_list}

For EACH criterion, decide pass or fail, and give a one-sentence reason citing specific evidence from the report.

Respond with ONLY valid JSON, no other text, in this exact format:
{{
  "results": [
    {{"criterion": "<criterion text>", "pass": true, "reason": "<why>"}},
    {{"criterion": "<criterion text>", "pass": false, "reason": "<why>"}}
  ]
}}"""

    response = llm.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": judge_prompt}]
    )

    raw_text = response.content[0].text.strip()

    # Defensive: strip markdown code fences if the model adds them despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("  [WARNING] Judge did not return valid JSON:")
        print(raw_text)
        return {"results": []}


if __name__ == "__main__":
    # Quick standalone test with a deliberately flawed fake report
    test_topic = "Why is Haruki Murakami considered a renowned author?"
    test_criteria = [
        "Every factual claim has an inline citation marker like [1], [2], etc.",
        "The report includes a complete Sources section with real URLs",
    ]
    test_report = "Murakami is famous because his books sell well and critics love him."

    result = judge_report(test_topic, test_criteria, test_report)
    print(json.dumps(result, indent=2))