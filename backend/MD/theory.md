# Video Agent - Theory and Architecture

## Overview

Video Agent is an AI-powered application that allows users to interact with YouTube videos through natural language.

Instead of manually watching long videos, users can provide a YouTube URL, and the system will:

1. Download the video audio.
2. Convert it into a Whisper-compatible format.
3. Generate a transcript using Speech-to-Text.
4. Translate non-English content into English.
5. Create embeddings from the transcript.
6. Store embeddings in a vector database.
7. Answer user questions using Retrieval-Augmented Generation (RAG).

---

# System Workflow

```text
YouTube URL
     ↓
Audio Download (yt-dlp)
     ↓
Audio Processing (FFmpeg)
     ↓
Chunking
     ↓
Whisper Transcription
     ↓
Translation (Hindi → English)
     ↓
Text Chunking
     ↓
Embeddings
     ↓
ChromaDB
     ↓
Retriever
     ↓
Mistral LLM
     ↓
Answer Generation
```

---

# Step 1: YouTube Audio Extraction

## Objective

Extract the highest-quality audio from a YouTube video.

## Tool Used

- yt-dlp

## Why yt-dlp?

yt-dlp is a powerful YouTube downloader that supports:

- Videos
- Audio streams
- Playlists
- Metadata extraction

The application downloads only the audio stream because speech transcription does not require video frames.

## Output

```text
video.wav
```

---

# Step 2: Audio Conversion

## Objective

Convert downloaded audio into a format optimized for speech recognition.

## Tool Used

- FFmpeg

## Why FFmpeg?

Audio downloaded from YouTube may have:

- Stereo channels
- Different sampling rates
- Different codecs

Speech recognition models perform best on standardized audio.

### Desired Format

```text
WAV
Mono
16 kHz
PCM
```

## Conversion Parameters

### Mono Audio

```text
-ac 1
```

Converts stereo audio into a single channel.

### Sampling Rate

```text
-ar 16000
```

Resamples audio to 16 kHz.

---

# Step 3: Audio Chunking

## Objective

Split long audio into manageable segments.

## Why Chunking?

Large audio files can:

- Increase memory consumption
- Slow transcription
- Cause timeout issues

Instead, audio is divided into smaller segments.

### Example

```text
30 Minute Audio

Chunk 1 → 0-10 min
Chunk 2 → 10-20 min
Chunk 3 → 20-30 min
```

## Tool Used

- pydub

---

# Step 4: Speech-to-Text

## Objective

Convert spoken audio into text.

## Tool Used

- OpenAI Whisper

## How Whisper Works

Whisper does not directly understand audio waves.

Internally it converts audio into a:

```text
Mel Spectrogram
```

A Mel Spectrogram is a visual representation of sound frequencies over time.

### Pipeline

```text
Audio
   ↓
Mel Spectrogram
   ↓
Transformer Model
   ↓
Text
```

## Output

```text
Hindi Transcript
```

Example:

```text
मुझे मशीन लर्निंग सीखना पसंद है।
```

---

# Step 5: Translation

## Objective

Convert transcript into English.

## Why?

Most LLMs perform best when working with English content.

## Translation Model

Possible options:

- IndicTrans2
- Gemini
- Deep Translator
- Mistral

### Example

Input:

```text
मुझे मशीन लर्निंग सीखना पसंद है।
```

Output:

```text
I like learning machine learning.
```

---

# Step 6: Text Chunking

## Objective

Split transcript into smaller text segments.

## Why?

LLMs and embedding models have context limitations.

Large transcripts are divided into chunks.

### Example

```text
Chunk 1
Chunk 2
Chunk 3
Chunk 4
```

## Tool Used

- LangChain Text Splitters

---

# Step 7: Embedding Generation

## Objective

Convert text into numerical vector representations.

## Why?

Machines cannot search efficiently through raw text.

Embeddings capture semantic meaning.

Example:

```text
"Artificial Intelligence"

↓

[0.24, -0.13, 0.88, ...]
```

## Tool Used

- Sentence Transformers
- HuggingFace Embeddings

---

# Step 8: Vector Database

## Objective

Store embeddings for semantic retrieval.

## Tool Used

- ChromaDB

## Why ChromaDB?

Traditional databases search exact words.

Vector databases search meaning.

### Example Query

```text
What is Machine Learning?
```

Even if transcript contains:

```text
Machines learn patterns from data.
```

the vector database can identify semantic similarity.

---

# Step 9: Retrieval-Augmented Generation (RAG)

## Objective

Provide context-aware answers.

## Process

```text
User Question
      ↓
Embedding
      ↓
Similarity Search
      ↓
Relevant Chunks Retrieved
      ↓
Context Sent to LLM
      ↓
Answer Generated
```

Without RAG:

```text
LLM guesses
```

With RAG:

```text
LLM answers using actual video content
```

---

# Step 10: Answer Generation

## Objective

Generate final responses.

## Model Used

- Mistral

## Responsibilities

- Summarization
- Question Answering
- Explanation
- Contextual Responses

Example:

Question:

```text
What is the main topic of the video?
```

Response:

```text
The video explains the fundamentals of machine learning,
including supervised learning, datasets, and model training.
```

---

# Why This Architecture?

This architecture combines:

### Speech Recognition

Whisper

### Translation

Indic Language Translation Models

### Semantic Search

Embeddings + ChromaDB

### Reasoning

Mistral LLM

### Retrieval

RAG Pipeline

This ensures:

- Accurate answers
- Lower hallucination rates
- Video-specific responses
- Multilingual support
- Scalability for long videos

---

# Tech Stack

| Component        | Technology                    |
| ---------------- | ----------------------------- |
| Audio Download   | yt-dlp                        |
| Audio Processing | FFmpeg                        |
| Audio Chunking   | pydub                         |
| Speech-to-Text   | Whisper                       |
| Translation      | IndicTrans2 / Deep Translator |
| Text Splitting   | LangChain                     |
| Embeddings       | Sentence Transformers         |
| Vector Store     | ChromaDB                      |
| LLM              | Mistral                       |
| Backend          | Python                        |
| Frontend         | Streamlit                     |
| Deployment       | Vercel + Backend API          |

---

# Final Data Flow

```text
YouTube Video
      ↓
yt-dlp
      ↓
FFmpeg
      ↓
WAV Audio
      ↓
Chunking
      ↓
Whisper
      ↓
Transcript
      ↓
Translation
      ↓
Text Chunks
      ↓
Embeddings
      ↓
ChromaDB
      ↓
Retriever
      ↓
Mistral
      ↓
Final Answer
```
