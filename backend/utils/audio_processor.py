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
    
    return filename

# wave_path = download_youtube_audio("https://www.youtube.com/watch?v=2jU-mLMV8Vw")


## The following function converts wav format to whisper ready, but we will modify the above function for doing that. This func is for local file path
def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path

def chunk_audio(wav_path:str,chunk_minutes:int = 10) -> list:
    # loads the entire wav file
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes*60*1000
    
    chunks = []
    
    #len(audio) is given in ms by pydub
    # i = 0, start = 0
    # i = 1, start = 600000
    # i = 2, start = 1200000
    for i, start in enumerate(range(0,len(audio), chunk_ms)):
        # slicing of audio
        # 0,600000 600000,1200000
        chunk = audio[start:start+chunk_ms]
        # Save the audio chunk as a WAV file on disk, else it is just on memory
        chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

# chunk_audio(wave_path)

def process_input(source: str)->list:
    if source.startswith("https://") or source.startswith("http://"):
        print("Detected youtube video URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)
        
    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio Ready - {len(chunks)} chunks(s) created!!!!")
    return chunks

# process_input("https://www.youtube.com/watch?v=2jU-mLMV8Vw")