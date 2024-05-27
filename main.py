from client import Client
from audio_streaming import KeyedStreamingAudioRecorder
from config import WHISPER_HOST, GPT_HOST
import sys
import time

def typewriter_effect(sequence, delay=None):
    tokens = []
    i = 0 
    for t in sequence:
        t = t.decode('utf-8')
        if '\n' in t:
            t = t.replace('\n',' -- ')
        tokens.append(t)
        text = ''.join(tokens)
        sys.stdout.write('\r' + text)
        if delay:
            time.sleep(delay)
   


def run():
    streaming_recorder = KeyedStreamingAudioRecorder(key='r',
                                                     server_ip=WHISPER_HOST)
    streaming_recorder.standby(one_shot=False)
    while True:
        prompt = streaming_recorder.q.get()
        client = Client(GPT_HOST, 5000)
        client.send(prompt)
        token_seq = client.receive_stream()
        typewriter_effect(token_seq)
