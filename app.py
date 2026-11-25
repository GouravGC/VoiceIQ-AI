import json
import os
import tempfile
import time
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

from app_core.transcriber import get_transcriber, transcribe_audio
from app_core.analysis import analyze_transcript

load_dotenv()

st.set_page_config(page_title="VoiceIQ AI", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem;}
.hero {padding: 1.5rem; border: 1px solid rgba(128,128,128,.25); border-radius: 16px;
       background: linear-gradient(120deg, rgba(59,130,246,.12), rgba(16,185,129,.08));}
.metric-card {padding: 1rem; border: 1px solid rgba(128,128,128,.25); border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🎙️ VoiceIQ AI</h1><p>Local speech-to-text and interview conversation intelligence</p></div>', unsafe_allow_html=True)
st.caption("Powered by Qwen3-ASR 1.7B through Ollama · Local inference · No transcription API key")

config = get_transcriber()

with st.sidebar:
    st.header("Transcription settings")
    st.text_input("Engine", value="Ollama · Qwen3-ASR 1.7B", disabled=True)
    st.text_input("Model", value=config["model"], disabled=True)
    st.caption("Language detection is automatic. Audio is normalized to 16 kHz mono WAV and processed in chunks of up to 55 seconds.")
    if st.button("Check local Ollama connection", use_container_width=True):
        try:
            health = requests.get(f"{config['base_url']}/api/tags", timeout=5)
            health.raise_for_status()
            models = [item.get("name", "") for item in health.json().get("models", [])]
            if any(config["model"] == name or config["model"].split(":")[0] == name.split(":")[0] for name in models):
                st.success("Ollama is reachable and the configured model is installed.")
            else:
                st.warning("Ollama is reachable, but the configured model was not found. Run: ollama list")
        except requests.RequestException:
            st.error(f"Cannot reach Ollama at {config['base_url']}. Start Ollama first.")
    st.divider()
    st.caption("This local setup requires Ollama and FFmpeg to be running/installed on the machine executing VoiceIQ.")

transcribe_tab, about_tab = st.tabs(["🎧 Transcribe audio", "ℹ️ About & evaluation"])

with transcribe_tab:
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    uploaded = st.file_uploader(
        "Upload an audio or video recording",
        type=["wav", "mp3", "m4a", "mp4", "mpeg", "mpga", "webm", "ogg", "flac", "mpg", "mpeg4"],
        help=f"Maximum configured upload size: {max_upload_mb} MB. Audio is processed locally by Ollama.",
    )
    if uploaded:
        st.audio(uploaded)
        if st.button("Transcribe with local AI", type="primary", use_container_width=True):
            suffix = Path(uploaded.name).suffix or ".audio"
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getbuffer())
                    temp_path = tmp.name

                with st.spinner("Preparing audio and transcribing with Qwen3-ASR locally…"):
                    start = time.perf_counter()
                    model_config = get_transcriber()
                    result = transcribe_audio(model_config, temp_path)
                    elapsed = time.perf_counter() - start

                st.session_state["voiceiq_result"] = result
                st.session_state["voiceiq_elapsed"] = elapsed
                st.session_state["voiceiq_filename"] = uploaded.name
                st.session_state.pop("voiceiq_analysis", None)
            except Exception as exc:
                st.error(f"Transcription failed: {exc}")
                st.info("Confirm Ollama is running, Qwen3-ASR is installed, and FFmpeg is available in PATH.")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    result = st.session_state.get("voiceiq_result")
    if result:
        st.success(f"Transcription completed · {st.session_state.get('voiceiq_filename', 'Audio')}")
        elapsed = st.session_state.get("voiceiq_elapsed", 0.0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Audio duration", f"{result.get('duration', 0.0):.1f}s")
        c2.metric("Processing time", f"{elapsed:.1f}s")
        c3.metric("Detected language", result.get("language") or "Auto-detected / unknown")

        transcript = result.get("text", "")
        st.subheader("Transcript")
        st.text_area("Recognized speech", transcript, height=240, label_visibility="collapsed")
        st.download_button("⬇️ Download transcript (.txt)", transcript,
                           file_name="voiceiq_transcript.txt", mime="text/plain")
        st.download_button("⬇️ Download transcript details (.json)",
                           json.dumps(result, ensure_ascii=False, indent=2),
                           file_name="voiceiq_transcript.json", mime="application/json")

        st.subheader("Chunk-level transcript segments")
        st.caption("Times identify the audio chunks processed. They are not word-level alignment timestamps.")
        for segment in result.get("segments", []):
            st.markdown(f"**[{segment['start']:.2f}s – {segment['end']:.2f}s]**  {segment['text']}")

        st.divider()
        st.subheader("Interview / conversation analysis")
        st.caption("Optional LLM analysis. It is separate from local transcription and may use your configured OpenRouter API key.")
        if st.button("Analyze transcript", use_container_width=True):
            with st.spinner("Analyzing transcript…"):
                try:
                    st.session_state["voiceiq_analysis"] = analyze_transcript(transcript)
                except Exception as exc:
                    st.error(str(exc))
        analysis = st.session_state.get("voiceiq_analysis")
        if analysis:
            st.markdown(analysis)
    else:
        st.info("Upload an audio file to get started. For best results, test a short, clear recording first.")

with about_tab:
    st.subheader("Built for practical speech AI engineering")
    st.markdown("""
- **Speech recognition:** Qwen3-ASR 1.7B (community Ollama package), running locally.
- **Audio preprocessing:** FFmpeg conversion to 16 kHz, mono, 16-bit PCM WAV.
- **Long recordings:** Automatic chunking into requests shorter than 60 seconds.
- **Language detection:** Automatic model detection; the published language list does not include Punjabi.
- **Exports:** Plain-text transcript and JSON metadata with chunk-level offsets.
- **Optional NLP:** OpenRouter-powered transcript summary and evidence extraction.
- **Evaluation:** Word Error Rate (WER) utility and processing-time measurements.

Audio transcription does not require an API key. The Ollama model must be installed on the same machine as the application, or be reachable through a private Ollama endpoint. A cloud-hosted Streamlit instance cannot reach your PC's `localhost` Ollama service.

**Responsible use:** VoiceIQ supports transcription and conversation review; it is not an automated hiring decision system. Human review is required for consequential decisions.
""")
    st.code(f"Provider: Ollama (local)\nModel: {config['model']}\nAudio: 16 kHz / mono / PCM WAV\nChunk size: 55 seconds", language="text")
