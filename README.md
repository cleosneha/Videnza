# Videnza — AI Video Assistant

Turn any video into actionable intelligence. Paste a YouTube link or pick a local file — Videnza transcribes it, distills key insights, and lets you ask questions about the content through a RAG-powered chatbot.

---

## Features

- **YouTube & Local Files** — Download audio from YouTube or process local video/audio files
- **Speech-to-Text** — English transcription via Groq Whisper; Hinglish via Sarvam AI
- **Smart Summarization** — Map-reduce summarization using Mistral AI
- **Insight Extraction** — Automatically extract action items, key decisions, and open questions
- **RAG Chat** — Ask questions about the video content using a retrieval-augmented generation pipeline
- **Web UI (Streamlit)** — Clean dark-themed interface with pipeline progress tracking
- **PDF Export** — Download transcripts and insights as PDFs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Frontend | Streamlit |
| STT | Groq Whisper, Sarvam AI |
| LLM | Mistral (`mistral-small-latest`) |
| Embeddings | Mistral (`mistral-embed`) |
| Vector DB | Pinecone |
| Audio | yt-dlp, FFmpeg, pydub |
| Framework | LangChain |

---

## Quick Start

```bash
# Clone
git clone <repo-url>
cd "Video Agent/backend"

# Setup
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt

# Configure API keys in .env (see SETUP.md for details)

# Run
streamlit run app.py
```

See [SETUP.md](SETUP.md) for a complete step-by-step guide.
