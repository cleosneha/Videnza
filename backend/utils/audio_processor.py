import os
from pathlib import Path

import yt_dlp
from pydub import AudioSegment


def download_youtube_audio(url: str, output_dir: str) -> str:
    output_path = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": [
        "-ac", "1",      # mono
        "-ar", "16000"   # 16kHz
        ],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base = os.path.splitext(ydl.prepare_filename(info))[0]
        filename = base + ".wav"

    return filename


def convert_to_wav(input_path: str, output_dir: str) -> str:
    """Convert any audio/video file to a mono 16kHz WAV inside the request temp directory."""
    input_name = Path(input_path).stem
    output_path = os.path.join(output_dir, f"{input_name}_converted.wav")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, output_dir: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    base_name = Path(wav_path).stem

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_path = os.path.join(output_dir, f"{base_name}_chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str, output_dir: str) -> list:
    if source.startswith("https://") or source.startswith("http://"):
        #print("Detected youtube video URL. Downloading audio...")
        wav_path = download_youtube_audio(source, output_dir=output_dir)
    else:
        #print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source, output_dir=output_dir)

    try:
        #print("Chunking audio...")
        chunks = chunk_audio(wav_path, output_dir=output_dir)
        #print(f"Audio Ready - {len(chunks)} chunks(s) created!!!!")
        return chunks
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
