import whisper
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None


def save_transcript(text: str, output_path: str = "downloads/full_transcript.txt") -> str:
    path = Path(output_path)
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)

def load_model():
    global _model
    if _model is None:
        print(f"Loading model....")
        _model = whisper.load_model(WHISPER_MODEL)
        print("whisper model loaded successfully")
        
    return _model

def transcribe_chunk(chunk_path: str, translate: bool = False)->str:
    model = load_model()
    task = "translate" if translate else "transcribe"
    result = model.transcribe(chunk_path, task = task)
    return result['text']
    
    
def transcribe_all(chunks: list, translate: bool = False) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}")
        text = transcribe_chunk(chunk, translate=translate)
        if text.strip():
            parts.append(text.strip())

    full_transcript = " ".join(parts)
    print("Transcription completed")
    return full_transcript

