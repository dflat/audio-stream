import wave
from ..config import CHANNELS, AUDIO_SAMPLE_RATE

def save_wav(buffer,
             wav_file_path,
             channels=CHANNELS,
             sample_width=2,
             frame_rate=AUDIO_SAMPLE_RATE):

    wf = wave.open(wav_file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(frame_rate)
    wf.writeframes(buffer)
    wf.close()
