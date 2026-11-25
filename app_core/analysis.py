import os
import requests


def analyze_transcript(transcript: str) -> str:
    """Optional LLM-powered transcript analysis; transcription remains local."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Transcript analysis is optional and needs OPENROUTER_API_KEY. "
            "Local Ollama transcription works without this key."
        )

    model = os.getenv(
        "OPENROUTER_ANALYSIS_MODEL",
        os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
    )
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
            "X-Title": "VoiceIQ AI",
        },
        json={
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Analyze the supplied conversation transcript. Return concise Markdown with: "
                        "1) Summary, 2) Key topics, 3) Questions asked, 4) Answers/evidence present, "
                        "5) Follow-up questions. Do not infer personality, competence, honesty, emotion, "
                        "or candidate suitability from accent, gender, identity, or speaking style. "
                        "Clearly mark information that is not present in the transcript."
                    ),
                },
                {"role": "user", "content": transcript[:30000]},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("The analysis model returned an empty response.")
    return content
