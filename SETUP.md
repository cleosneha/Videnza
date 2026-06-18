# Videnza — AI Video Assistant Setup Guide

> **Videnza** is an AI-powered video assistant that downloads YouTube videos (or accepts local files), transcribes them, summarizes the content, extracts action items/decisions/questions, and provides a Q&A chatbot over the video using RAG.

---

## Prerequisites

Make sure the following are installed on your machine **before** starting:

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.12+ | [Download Python](https://www.python.org/downloads/) |
| **FFmpeg** | Latest | Required for audio processing. [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system `PATH` |
| **Git** | Latest | [Download Git](https://git-scm.com/downloads) |
| **uv** (optional) | Latest | Faster alternative to `pip`. Install via `pip install uv` |

---

## Step 1 — Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd Video Agent
```

> Replace the URL with the actual repository URL.

---

## Step 2 — Set Up a Virtual Environment

Navigate to the `backend` folder:

```bash
cd backend
```

Create a virtual environment (choose one):

**Option A — Using `uv` (recommended, faster):**

```bash
uv venv --python 3.12
```

**Option B — Using standard `venv`:**

```bash
python -m venv .venv
```

Activate the environment:

- **Windows (Git Bash / CMD):**
  ```bash
  source .venv/Scripts/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

You should see `(.venv)` at the start of your terminal prompt.

---

## Step 3 — Install Dependencies

With the virtual environment activated, run:

```bash
pip install -r requirements.txt
```

> If you have `uv` installed, you can use `uv pip install -r requirements.txt` for faster installation.

---

## Step 4 — Get Your API Keys

This project requires **four** API keys / credentials. Sign up for each service and get your keys:

### 4.1 Groq API Key (for English transcription)

1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up / log in
3. Create an API key from the dashboard

### 4.2 Mistral AI API Key (for summarization, extraction, RAG, embeddings)

1. Go to [console.mistral.ai](https://console.mistral.ai/)
2. Sign up / log in
3. Go to **API Keys** section and create a new key

### 4.3 Sarvam AI API Key (for Hinglish transcription)

1. Go to [sarvam.ai](https://sarvam.ai/)
2. Sign up / log in
3. Navigate to the API section and generate a key

> Note: If you only need **English** transcription, you can skip Sarvam and just set an empty value for `SARVAM_API_KEY`.

### 4.4 Pinecone API Key (for vector database)

1. Go to [pinecone.io](https://www.pinecone.io/)
2. Sign up / log in (free tier is sufficient)
3. Create an API key
4. Note your **Index Name** and **Index Host** (or let the app create it automatically)

---

## Step 5 — Configure Environment Variables

Inside the `backend/` folder, create a file named `.env`:

```bash
# backend/.env

# Groq (Whisper STT)
GROQ_API_KEY="your_groq_api_key_here"
GROQ_TRANSCRIPTION_MODEL="whisper-large-v3"

# Mistral AI (Summarization, Extraction, RAG, Embeddings)
MISTRAL_API_KEY="your_mistral_api_key_here"

# Sarvam AI (Hinglish STT) — optional for English-only usage
SARVAM_API_KEY="your_sarvam_api_key_here"
SARVAM_STT_MODEL="saaras:v2.5"

# Pinecone (Vector Database)
PINECONE_API_KEY="your_pinecone_api_key_here"
PINECONE_INDEX_NAME="video-assistant"
PINECONE_INDEX_HOST="https://your-index-host.pinecone.io"
PINECONE_CLOUD="aws"
PINECONE_REGION="us-east-1"
```

> **⚠️ Security Warning:** Never commit the `.env` file to Git. The repository already has `.env` in `.gitignore`, so it will be ignored automatically.

---

## Step 6 — Run the Application

You have two ways to use Videnza:

### 6.1 Web UI (Streamlit)

```bash
streamlit run app.py
```

This will open a browser tab with the Videnza interface. You can:
- Paste a YouTube URL or provide a local video file path
- Select language (English or Hinglish)
- View transcription, summary, action items, decisions, and questions
- Chat with the video using the RAG chatbot

### 6.2 Command Line Interface

```bash
python main.py
```

You will be prompted for:
- Video source (YouTube URL or local file path)
- Language (english/hinglish)

After processing, you can ask questions interactively.

---

## Project Structure

```
Video Agent/
├── README.md
├── SETUP.md                  ← You are here
├── .gitignore
└── backend/
    ├── .env                  ← Your API keys (not committed)
    ├── requirements.txt      ← Python dependencies
    ├── app.py                ← Streamlit web UI
    ├── main.py               ← CLI entry point
    ├── core/
    │   ├── transcriber.py    ← Speech-to-text (Groq / Sarvam)
    │   ├── summarize.py      ← Map-reduce summarization
    │   ├── extractor.py      ← Action items, decisions, questions
    │   ├── RAG_Engine.py     ← Q&A chatbot over video
    │   ├── vector_store.py   ← Pinecone vector store ops
    │   └── namespace_manager.py ← Namespace lifecycle
    └── utils/
        └── audio_processor.py ← YouTube download + audio chunking
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ffmpeg` not found | Install FFmpeg and ensure it is added to your system `PATH`. Restart your terminal after installing. |
| `pip install` fails | Upgrade pip: `pip install --upgrade pip`. On Windows, you may need to install Microsoft C++ Build Tools. |
| Pinecone index not found | The app can create the index automatically if the `PINECONE_INDEX_NAME` does not exist. Ensure your Pinecone account has serverless index capability. |
| No audio from YouTube | Some YouTube videos are region-restricted or copyright-blocked. Try a different video. |
| Quota exceeded | Free API tiers have rate limits. Wait a while or upgrade your accounts. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Frontend | Streamlit |
| Speech-to-Text | Groq Whisper (English), Sarvam AI (Hinglish) |
| LLM | Mistral (`mistral-small-latest`) |
| Embeddings | Mistral (`mistral-embed`) |
| Vector Database | Pinecone (Serverless, AWS) |
| Audio Download | yt-dlp |
| Audio Processing | FFmpeg + pydub |
| Framework | LangChain |
