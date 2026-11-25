from app_core.transcriber import (
    DEFAULT_MODEL,
    _parse_model_response,
    get_transcriber,
    transcribe_audio,
)


def test_transcriber_module_imports():
    assert callable(transcribe_audio)


def test_default_transcriber_uses_local_qwen_asr(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    config = get_transcriber()
    assert config["provider"] == "ollama"
    assert config["model"] == DEFAULT_MODEL
    assert config["base_url"] == "http://localhost:11434"


def test_parse_qwen_asr_response_with_language_marker():
    text, language = _parse_model_response("language Hindi<asr_text>नमस्ते दुनिया")
    assert text == "नमस्ते दुनिया"
    assert language == "Hindi"


def test_parse_qwen_asr_response_without_language_marker():
    text, language = _parse_model_response("Recognized words here")
    assert text == "Recognized words here"
    assert language is None


def test_legacy_whisper_size_does_not_override_ollama_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "frozenlab/qwen3-asr:1.7b")
    assert get_transcriber("tiny")["model"] == "frozenlab/qwen3-asr:1.7b"
