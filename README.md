# VoiceIQ AI

**Local-first speech-to-text and conversation analysis** built with Streamlit, Ollama and Qwen3-ASR.

VoiceIQ converts uploaded audio/video into text using a locally running Qwen3-ASR model. Audio transcription does not require a paid transcription API or an API key.

## Features

- Audio/video upload and playback
- Local speech recognition using Qwen3-ASR 1.7B through Ollama
- Automatic language detection
- FFmpeg audio normalization (16 kHz, mono, 16-bit PCM WAV)
- Automatic chunking for longer recordings (55-second chunks)
- TXT transcript and JSON metadata downloads
- Optional transcript analysis using OpenRouter
- Word Error Rate (WER) evaluation utility
- Docker packaging and GitHub Actions CI

> Language note: the published Qwen3-ASR language list includes English and Hindi but does not list Punjabi. Validate performance on your own audio before claiming Punjabi support. Singing/music recognition is model-supported, but lyric accuracy depends on the recording.

## Architecture

```text
Browser / Streamlit UI
        |
        v
Upload + temporary file handling
        |
        v
FFmpeg: decode -> mono 16 kHz PCM WAV
        |
        v
55-second audio chunking
        |
        v
Ollama local API (localhost:11434)
        |
        v
Qwen3-ASR 1.7B -> transcript + detected language
        |
        +----> TXT / JSON export
        |
        +----> Optional OpenRouter transcript analysis
```

The `frozenlab/qwen3-asr` package is a community Ollama packaging of Qwen3-ASR with its audio encoder. It is not an official first-party Ollama model package.

## Requirements

- Windows 10/11, Linux or macOS
- Python 3.11
- Ollama with audio-projector support
- `frozenlab/qwen3-asr:1.7b` downloaded in Ollama
- FFmpeg installed and available on `PATH`
- Recommended local hardware: 16 GB RAM; a GPU is optional. The model package is approximately 2.5 GB on disk.

## Windows CMD setup

```cmd
conda create -n voiceiq python=3.11.10 -y
conda activate voiceiq
```

Install FFmpeg if it is not already installed. For example, with Windows Package Manager:

```cmd
winget install Gyan.FFmpeg
```

Close and reopen CMD, then verify:

```cmd
ffmpeg -version
ollama --version
ollama list
```

Download the model once if needed:

```cmd
ollama pull frozenlab/qwen3-asr:1.7b
```

Install Python dependencies and run:

```cmd
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Open `http://localhost:8501`. Keep Ollama running in the background. The application calls its local API at `http://localhost:11434` by default.

## Environment configuration

```env
TRANSCRIPTION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=frozenlab/qwen3-asr:1.7b
OLLAMA_TIMEOUT_SECONDS=180

# Optional transcript analysis only
OPENROUTER_API_KEY=
OPENROUTER_ANALYSIS_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
```

Do not commit `.env` or API keys. Transcription works without OpenRouter. Only the optional analysis button uses the OpenRouter key.

## Run with Docker (local machine)

The Docker image contains the app and FFmpeg, **not** the 2.5 GB Ollama model. Ollama must run on the host machine.

```cmd
docker build -t voiceiq-ai .
docker run --rm -p 8501:8501 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 voiceiq-ai
```

Open `http://localhost:8501`. On Linux Docker, configure the host-gateway mapping or set `OLLAMA_BASE_URL` to a reachable private Ollama endpoint.

## Public deployment status and limitation

The Streamlit interface can be hosted publicly, but a cloud container's `localhost` is the cloud container itself—not your Windows PC. Therefore, the public service cannot use the Ollama model installed on your PC without a separately reachable inference host. Do not expose Ollama's port `11434` directly to the public internet.

For a reliable public transcription demo, deploy the inference runtime on private GPU infrastructure or use a managed speech API. Until that is configured, describe this repository as a **local-first application with a cloud-deployment-ready UI**, not as a publicly hosted transcription service. A public UI-only deployment may be used for preview, but transcription will require a reachable Ollama endpoint.

## Evaluation and evidence

Use `word_error_rate(reference, hypothesis)` from `app_core.metrics` to compare a human-verified reference with the model transcript. Record results for each test clip; do not invent accuracy claims.

Suggested evaluation set:

| Test | Audio type | Ground truth | Metrics to record |
|---|---|---|---|
| 1 | Clear English speech | Manually verified | WER, latency |
| 2 | Hindi speech | Manually verified | WER, latency |
| 3 | Hindi-English code-switching | Manually verified | WER, language detection |
| 4 | Song with vocals | Verified lyrics | WER / qualitative notes |
| 5 | Punjabi speech/song | Manually verified | Unsupported-language stress test; document actual result |

Record model tag, audio duration, processing time, hardware, and any manual corrections. Chunk boundaries are shown as approximate segment offsets; they are not word-level forced-alignment timestamps.

## CI/CD

GitHub Actions runs unit tests on pushes and pull requests. A GitHub-hosted runner does not have your local Ollama model, so CI validates imports and pure functions without running model inference. A hosting provider can deploy the Streamlit UI after CI passes, but functional public transcription requires a separately reachable Ollama inference service.

## Responsible use

VoiceIQ is a transcription and conversation-support tool, not an automated hiring decision system. Do not infer candidate suitability, personality, honesty, emotion, or competence from accent, gender, identity, or speaking style. Human review is required for consequential decisions.

### Calculate WER from saved transcripts

Save a manually verified reference transcript and a VoiceIQ `.txt` export, then run:

```cmd
python scripts\evaluate_wer.py evaluation\reference.txt evaluation\voiceiq_transcript.txt
```

A blank results sheet is provided at `evaluation/results_template.csv`. Fill it only with measurements from actual runs; do not report the template as completed evaluation.
