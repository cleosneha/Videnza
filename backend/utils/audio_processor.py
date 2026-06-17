import os
import shutil
import tempfile
from pathlib import Path

import yt_dlp
from pydub import AudioSegment


COOKIE_FILE = "/etc/secrets/cookies.txt"


def download_youtube_audio(url: str, output_dir: str) -> str:
    output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,

        "cachedir": False,

        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb"]
            }
        },

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },

        "noplaylist": True,
        "geo_bypass": True,
        "quiet": True,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        "postprocessor_args": [
            "-ac", "1",
            "-ar", "16000"
        ],
    }

    temp_cookie_file = None

    try:
        if os.path.exists(COOKIE_FILE):
            temp_cookie_file = os.path.join(
                tempfile.gettempdir(),
                "youtube_cookies.txt"
            )

            shutil.copy(COOKIE_FILE, temp_cookie_file)

            ydl_opts["cookiefile"] = temp_cookie_file

            print("Using YouTube cookies.")
        else:
            print("cookies.txt not found. Continuing without cookies.")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            downloaded_file = ydl.prepare_filename(info)
            wav_file = os.path.splitext(downloaded_file)[0] + ".wav"

            if not os.path.exists(wav_file):
                raise RuntimeError(
                    "yt-dlp completed but WAV file was not generated."
                )

            return wav_file

    except Exception as e:
        raise RuntimeError(
            f"Failed to download YouTube audio. "
            f"The video may be restricted or blocked by YouTube. "
            f"Original error: {str(e)}"
        )

    finally:
        if (
            temp_cookie_file
            and os.path.exists(temp_cookie_file)
        ):
            os.remove(temp_cookie_file)


def convert_to_wav(input_path: str, output_dir: str) -> str:
    input_name = Path(input_path).stem

    output_path = os.path.join(
        output_dir,
        f"{input_name}_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(
    wav_path: str,
    output_dir: str,
    chunk_minutes: int = 10
) -> list:

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000
    base_name = Path(wav_path).stem

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = os.path.join(
            output_dir,
            f"{base_name}_chunk_{i}.wav"
        )

        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str, output_dir: str) -> list:
    if source.startswith(("https://", "http://")):
        wav_path = download_youtube_audio(
            source,
            output_dir=output_dir
        )
    else:
        wav_path = convert_to_wav(
            source,
            output_dir=output_dir
        )

    try:
        return chunk_audio(
            wav_path,
            output_dir=output_dir
        )
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)