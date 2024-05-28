from .. import config
import requests
import numpy as np
import time

class UnrealSpeech:
    api_key = config.API_KEY
    url = config.UNREALSPEECH_URL
    headers = {"accept": "text/plain", "content-type": "application/json", "Authorization": "Bearer " + api_key}

    @staticmethod
    def _make_payload(Text,
                      VoiceId="Scarlett",
                      Bitrate="192k",
                      Speed=0,
                      Pitch=1.0,
                      Codec="pcm_s16le",
                      Temperature=0.25):
        return locals()

    @staticmethod
    def get_audio(text: str, **kwargs) -> np.ndarray[np.int16]:
        payload = UnrealSpeech._make_payload(text, **kwargs)
        t = time.time()
        resp = requests.post(UnrealSpeech.url, json=payload, headers=UnrealSpeech.headers, stream=True)
        resp.raise_for_status()
        e = time.time()
        UnrealSpeech.dur = e-t
        return b''.join(resp.iter_content(4096))
        
        #return np.frombuffer(resp.content, np.int16)
        