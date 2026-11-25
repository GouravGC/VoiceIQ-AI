
import os
import re
import io
import time
import base64
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
import imageio_ffmpeg


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "frozenlab/qwen3-asr:1.7b"
)

DEFAULT_MODEL = OLLAMA_MODEL

SAMPLE_RATE = 16000
CHUNK_SECONDS = 55
REQUEST_TIMEOUT = 300


# ============================================================
# TRANSCRIBER CONFIGURATION
# ============================================================

def get_transcriber(model_size=None):
    """
    Return the local Ollama configuration.

    model_size is accepted for backward compatibility with
    older Whisper-based application code.
    """
    return {
        "provider": "ollama",
        "model": os.getenv("OLLAMA_MODEL", DEFAULT_MODEL),
        "base_url": os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        ).rstrip("/"),
        "device": "local",
    }


# ============================================================
# FFMPEG
# ============================================================

def get_ffmpeg_path():
    """
    Find FFmpeg either in PATH or through imageio-ffmpeg.
    """
    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError(
            "FFmpeg is unavailable. Install imageio-ffmpeg."
        ) from exc


def get_audio_duration(audio_path):
    """
    Get audio duration using FFmpeg.
    """
    ffmpeg = get_ffmpeg_path()

    command = [
        ffmpeg,
        "-i", str(audio_path),
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    output = result.stderr or ""

    match = re.search(
        r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
        output
    )

    if not match:
        return 0.0

    hours, minutes, seconds = match.groups()

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + float(seconds)
    )


# ============================================================
# AUDIO NORMALIZATION
# ============================================================

def normalize_audio(audio_path):
    """
    Convert audio to 16 kHz, mono, PCM WAV.

    Returns:
        Path to normalized WAV file.
        Temporary directory used for the conversion.
    """
    ffmpeg = get_ffmpeg_path()

    temp_dir = tempfile.mkdtemp(prefix="voiceiq_")
    output_path = Path(temp_dir) / "normalized.wav"

    command = [
        ffmpeg,
        "-y",
        "-i", str(audio_path),
        "-vn",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        str(output_path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not output_path.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

        raise RuntimeError(
            "Audio normalization failed: "
            + (result.stderr[-2000:] if result.stderr else "Unknown FFmpeg error")
        )

    return str(output_path), temp_dir


# ============================================================
# AUDIO CHUNKING
# ============================================================

def split_audio(audio_path):
    """
    Split normalized WAV audio into chunks.

    Each chunk is at most CHUNK_SECONDS long.
    Returns a list of (chunk_path, start_time, end_time).
    """
    ffmpeg = get_ffmpeg_path()

    duration = get_audio_duration(audio_path)

    if duration <= 0:
        raise RuntimeError("Could not determine audio duration.")

    temp_dir = tempfile.mkdtemp(prefix="voiceiq_chunks_")
    chunks = []

    start = 0.0
    index = 0

    while start < duration:
        end = min(start + CHUNK_SECONDS, duration)

        chunk_path = Path(temp_dir) / f"chunk_{index:04d}.wav"

        command = [
            ffmpeg,
            "-y",
            "-ss", str(start),
            "-i", str(audio_path),
            "-t", str(end - start),
            "-ac", "1",
            "-ar", str(SAMPLE_RATE),
            "-c:a", "pcm_s16le",
            str(chunk_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not chunk_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

            raise RuntimeError(
                f"Failed to create audio chunk {index}: "
                + (result.stderr[-1000:] if result.stderr else "Unknown error")
            )

        chunks.append((str(chunk_path), start, end))

        start = end
        index += 1

    return chunks, temp_dir


# ============================================================
# RESPONSE PARSING
# ============================================================

def _parse_model_response(content):
    """
    Extract transcript and language from Qwen3-ASR response.
    """
    content = (content or "").strip()

    language = None

    language_match = re.search(
        r"language\s+([^\s<]+)",
        content,
        flags=re.IGNORECASE
    )

    if language_match:
        language = language_match.group(1).strip()

    if "<asr_text>" in content:
        content = content.split("<asr_text>", 1)[1]

    content = re.sub(
        r"</?asr_text>",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(r"<\|[^|]*\|>", "", content)

    return content.strip(), language


def parse_transcription(content):
    """
    Backward-compatible transcript parser.
    """
    text, language = _parse_model_response(content)

    return {
        "text": text,
        "language": language
    }


# ============================================================
# OLLAMA CONNECTION
# ============================================================

def check_ollama():
    """
    Check whether Ollama is running and the configured model
    is installed.
    """
    config = get_transcriber()

    try:
        response = requests.get(
            f"{config['base_url']}/api/tags",
            timeout=10
        )

        response.raise_for_status()

        models = response.json().get("models", [])

        installed_names = [
            model.get("name", "")
            for model in models
        ]

        configured_model = config["model"]

        model_installed = any(
            name == configured_model
            or name.split(":")[0] == configured_model.split(":")[0]
            for name in installed_names
        )

        return {
            "available": True,
            "model_installed": model_installed,
            "model": configured_model,
            "installed_models": installed_names,
            "error": None
        }

    except requests.RequestException as exc:
        return {
            "available": False,
            "model_installed": False,
            "model": config["model"],
            "installed_models": [],
            "error": str(exc)
        }


# ============================================================
# SINGLE CHUNK TRANSCRIPTION
# ============================================================

def transcribe_chunk(audio_path, model=None):
    """
    Transcribe one WAV chunk using the local Ollama Qwen3-ASR
    model.

    The model package expects base64 audio in the images field.
    """
    config = get_transcriber()

    selected_model = model or config["model"]

    with open(audio_path, "rb") as audio_file:
        audio_base64 = base64.b64encode(
            audio_file.read()
        ).decode("utf-8")

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Transcribe the audio accurately. "
                    "Identify the spoken language. "
                    "Return the recognized words without "
                    "summarizing or translating."
                ),
                "images": [audio_base64]
            }
        ],
        "stream": False
    }

    response = requests.post(
        f"{config['base_url']}/api/chat",
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: "
            f"{response.text[:2000]}"
        )

    data = response.json()

    content = (
        data.get("message", {}).get("content", "")
        or data.get("response", "")
    )

    transcript, language = _parse_model_response(content)

    if not transcript:
        raise RuntimeError(
            "The ASR model returned an empty transcription."
        )

    return {
        "text": transcript,
        "language": language
    }


# ============================================================
# FULL AUDIO TRANSCRIPTION
# ============================================================


def transcribe_audio(audio_path, model_size=None, **kwargs):
    """
    Transcribe using local Ollama Qwen3-ASR.

    Supports:
        transcribe_audio(audio_path)
        transcribe_audio(audio_path, config)
        transcribe_audio(config, audio_path)
    """
    started_at = time.time()

    # Handle legacy application calling convention:
    # transcribe_audio(config, audio_path)
    if isinstance(audio_path, dict):
        config_arg = audio_path
        audio_path = model_size
        model_size = None

        if isinstance(audio_path, dict):
            raise TypeError("Audio path is missing.")

        if not isinstance(audio_path, (str, Path)):
            raise TypeError("Invalid audio path.")

        config = get_transcriber()
        config.update(config_arg)

    else:
        config = get_transcriber()

        # Handle transcribe_audio(audio_path, config)
        if isinstance(model_size, dict):
            config.update(model_size)

    audio_path = str(audio_path)

    if not Path(audio_path).is_file():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    connection = check_ollama()

    if not connection["available"]:
        raise RuntimeError(
            f"Cannot connect to Ollama: {connection['error']}"
        )

    if not connection["model_installed"]:
        raise RuntimeError(
            f"Model '{config['model']}' is not installed."
        )

    normalized_path = None
    normalization_dir = None
    chunk_dir = None

    try:
        normalized_path, normalization_dir = normalize_audio(
            audio_path
        )

        duration = get_audio_duration(normalized_path)

        chunks, chunk_dir = split_audio(normalized_path)

        transcript_parts = []
        segments = []
        detected_language = None

        for index, (chunk_path, start, end) in enumerate(chunks):
            result = transcribe_chunk(
                chunk_path,
                model=config["model"]
            )

            chunk_text = result["text"].strip()

            if chunk_text:
                transcript_parts.append(chunk_text)

                segments.append({
                    "id": index,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "text": chunk_text
                })

            if result.get("language") and not detected_language:
                detected_language = result["language"]

        full_text = " ".join(transcript_parts).strip()

        if not full_text:
            raise RuntimeError("No transcription was produced.")

        return {
            "text": full_text,
            "language": detected_language or "Unknown",
            "language_probability": None,
            "duration": duration,
            "processing_time": round(time.time() - started_at, 2),
            "provider": "Ollama (Local)",
            "model": config["model"],
            "segments": segments,
            "word_segments": []
        }

    finally:
        if chunk_dir:
            shutil.rmtree(chunk_dir, ignore_errors=True)

        if normalization_dir:
            shutil.rmtree(normalization_dir, ignore_errors=True)
