from .. import config
import requests
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class UnrealSpeech:
    api_key = config.API_KEY
    url = config.UNREALSPEECH_URL
    headers = {"accept": "text/plain", "content-type": "application/json", "Authorization": "Bearer " + api_key}

    @staticmethod
    def _make_payload(Text,
                      VoiceId="Will",
                      Bitrate="192k",
                      Speed=0,
                      Pitch=0.92,
                      Codec="pcm_s16le",
                      Temperature=0.25):
        return locals()


    @staticmethod
    def get_stream(text:str, **kwargs) -> 'Response':
        payload = UnrealSpeech._make_payload(text, **kwargs)
        logger.info("request sent to UnrealSpeech")
        start = time.time()
        resp = requests.post(url=UnrealSpeech.url,
                             json=payload,
                             headers=UnrealSpeech.headers,
                             stream=True)
        resp.raise_for_status()
        end = time.time()
        logger.info(f'response received after {end-start:.1f} seconds.')
        return resp