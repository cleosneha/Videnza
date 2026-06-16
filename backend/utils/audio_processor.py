import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIRECTORY = 'downloads'
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

def download_youtube_audio(url :str) ->str:
    output_path = os.path.join(DOWNLOAD_DIRECTORY, "%(title)s.%(ext)s")
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
    audio = AudioSegment.from_file(filename)

    print("Channels:", audio.channels)
    print("Frame Rate:", audio.frame_rate)
    return filename

print(download_youtube_audio("https://www.youtube.com/watch?v=fCHe_fOqlYA"))


## The following function converts wav format to whisper ready, but we will modify the above function for doing that.
# def convert_to_wav(input_path: str) -> str:
#     """Convert any audio/video file to WAV format using pydub."""
#     output_path = os.path.splitext(input_path)[0] + "_converted.wav"
#     audio = AudioSegment.from_file(input_path)
#     audio = audio.set_channels(1).set_frame_rate(16000) #16khz
#     audio.export(output_path, format="wav")
#     return output_path
