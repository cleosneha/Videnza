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
        "format": "bestaudio",
        "outtmpl": output_path,
        "quiet": True,
        "cachedir": False,

        "noplaylist": True,
        "geo_bypass": True,


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

            filename = os.path.splitext(downloaded_file)[0] + ".wav"

            if not os.path.exists(filename):
                raise RuntimeError(
                    f"WAV file not found after download: {filename}"
                )

            return filename

    except Exception as e:
        raise RuntimeError(
            f"Failed to download YouTube audio. Original error: {str(e)}"
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
) -> list[str]:

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


def process_input(
    source: str,
    output_dir: str,
) -> list[str]:

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