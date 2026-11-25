# 🎙️ VoiceIQ AI
### Local-First Speech-to-Text & Conversation Intelligence

VoiceIQ AI is a local-first speech-to-text application built with Python, Streamlit, Ollama, and Qwen3-ASR 1.7B.

It converts uploaded audio and video into text using locally hosted AI inference, with automatic language detection, audio preprocessing, and chunk-based transcription.

**The primary objective is to provide speech transcription without depending on paid transcription APIs or sending audio recordings to an external transcription service.**

---

## 🚀 Features

- **Local AI Transcription:** Speech recognition using Qwen3-ASR 1.7B through Ollama.
- **Automatic Language Detection:** Detects the language of the audio during transcription.
- **Audio & Video Upload:** Supports common audio and video formats.
- **Audio Preprocessing:** FFmpeg-based conversion to 16 kHz mono WAV.
- **Long Audio Processing:** Automatically splits longer recordings into manageable 55-second chunks.
- **Transcript Export:** Download generated transcripts and associated metadata.
- **Optional AI Analysis:** OpenRouter integration for additional transcript analysis.
- **Evaluation Utilities:** Word Error Rate (WER) evaluation support.
- **Interactive Interface:** Streamlit-based user interface.

## 🧠 Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Frontend | Streamlit |
| Speech Recognition | Qwen3-ASR 1.7B |
| Local Model Runtime | Ollama |
| Audio Processing | FFmpeg |
| API Communication | Python Requests |
| Optional AI Analysis | OpenRouter |
| Testing | Pytest |
| Containerization | Docker |
| CI/CD | GitHub Actions |

## 🏗️ Architecture

```text
             User
              |
              v
       Streamlit Interface
              |
              v
       Audio / Video Upload
              |
              v
       FFmpeg Preprocessing
        16 kHz Mono WAV
              |
              v
        Audio Chunking
         55-second chunks
              |
              v
       Ollama Local API
        localhost:11434
              |
              v
        Qwen3-ASR 1.7B
              |
              v
      Transcription Output
              |
       +------+------+
       |             |
       v             v
   TXT / JSON    Optional AI
     Export       Analysis
```

## ⚙️ Local Installation

### Prerequisites

- Python 3.11
- Ollama installed and running
- FFmpeg available on the system
- Sufficient RAM and storage for the selected model
- Git

### 1. Clone the repository

```bash
git clone https://github.com/GouravGC/VoiceIQ-AI.git
cd VoiceIQ-AI
```

### 2. Create a virtual environment

Using Conda:

```bash
conda create -n voiceiq python=3.11.10 -y
conda activate voiceiq
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the ASR model

```bash
ollama pull frozenlab/qwen3-asr:1.7b
```

### 5. Configure environment variables

Copy the example environment file:

```bash
copy .env.example .env
```

Configure the local transcription settings:

```env
TRANSCRIPTION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=frozenlab/qwen3-asr:1.7b
```

Optional transcript analysis can be configured separately using an OpenRouter API key.

**Note:** Audio transcription itself does not require an OpenRouter API key.

### 6. Run the application

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Keep Ollama running while using VoiceIQ AI.

---

## 🖥️ Deployment Status — Why This Project Is Not Publicly Hosted

**VoiceIQ AI is intentionally maintained as a locally executable AI application rather than a publicly hosted transcription service.**

This is an architectural decision, not an incomplete transcription implementation.

The application depends on Ollama running on the same machine, or on a separately accessible machine hosting the inference service.

The Qwen3-ASR model is downloaded and executed locally through Ollama. A standard cloud deployment on platforms such as Render or Streamlit Community Cloud would not automatically have access to the model installed on a developer's computer.

For a functional public deployment, additional infrastructure would be required:

- A dedicated machine or GPU-enabled cloud instance.
- Ollama installed and configured on the inference host.
- The Qwen3-ASR model downloaded on that host.
- Secure connectivity between the Streamlit application and the inference service.
- Additional infrastructure costs and ongoing maintenance.

Deploying only the Streamlit interface without providing accessible inference infrastructure would result in a public application that cannot perform its primary transcription function.

**Therefore, public hosting has deliberately been deferred rather than presenting a UI-only deployment as a fully functional AI transcription service.**

The project can be executed locally by anyone who installs the required dependencies and downloads the model.

> Important: Ollama's local API should not be exposed directly to the public internet. A production deployment would require an appropriately secured inference service.

---

## 📊 Evaluation

VoiceIQ AI includes utilities for evaluating transcription quality using Word Error Rate (WER).

Suggested evaluation scenarios:

- English speech transcription.
- Hindi speech transcription.
- Multilingual and code-switched speech.
- Vocal-heavy music recordings.
- Longer audio recordings processed through chunking.

Actual accuracy depends on audio quality, background noise, language support, and the model's performance.

No unverified accuracy percentages are claimed.

## 🎬 Project Demonstration

A demonstration recording is maintained in the repository's `evidences/` directory.

The demonstration showcases the application interface, audio upload workflow, local transcription process, and generated transcript.

## 🔒 Privacy & Local Inference

- Audio transcription runs through the locally hosted Ollama model.
- Audio is processed on the machine executing the application.
- No paid transcription API is required.
- Optional OpenRouter transcript analysis is a separate feature and may send transcript text to an external API when explicitly used.

Do not commit private recordings, API keys, or `.env` files to GitHub.

## 🔮 Future Improvements

- More comprehensive multilingual transcription evaluation.
- Improved music and noisy-audio transcription benchmarks.
- Better timestamp alignment.
- Optional secure remote inference architecture.
- Expanded conversation intelligence and transcript