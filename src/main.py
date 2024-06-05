import sys
import time
from threading import Thread, Event
from .network import Client
from .audio_streaming import KeyedStreamingAudioRecorder
from .config import WHISPER_HOST, GPT_HOST, GPT_PORT
from .utils import SentenceParser
from .tts import fetch_and_play

def typewrite(sentence, delay=0.1):
    for word in sentence.split(' '):
        print(word, end=' ', flush=True)
        time.sleep(delay)

def play_and_type_text(sentence, type_transcript=True):
    if type_transcript:
        Thread(target=typewrite, args=(sentence,)).start()
    fetch_and_play(sentence)

def run():
    recorder = KeyedStreamingAudioRecorder(key='r', server_ip=WHISPER_HOST)
    recorder.standby(one_shot=False)
    parser = SentenceParser()
    sentence_thread = None

    while True:
        prompt = recorder.wait_for_input()

        client = Client(GPT_HOST, GPT_PORT)
        client.send(prompt)

        token_seq = client.receive_stream()
        sentence_seq = parser.get_sentences(token_seq)

        for sentence in sentence_seq:
            if sentence_thread:
                sentence_thread.join()
            sentence_thread = Thread(target=play_and_type_text, args=(sentence,))
            sentence_thread.start()
        sentence_thread.join()

        print(f"\n\n(token count: {parser.n_tokens})")
        parser.reset()

