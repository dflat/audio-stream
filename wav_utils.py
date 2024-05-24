import wave

def save_wav(buffer, wav_file_path, channels=2, sample_width=2, frame_rate=44100):
    wf = wave.open(wav_file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(frame_rate)
    wf.writeframes(buffer)
    wf.close()
