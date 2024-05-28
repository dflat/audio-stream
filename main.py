from client import Client
from audio_streaming import KeyedStreamingAudioRecorder
from config import WHISPER_HOST, GPT_HOST, GPT_PORT
from parsing import SentenceParser
import sys
import time
from threading import Thread, Event

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
   

def typewrite(sentence, done_event=None, delay=0.1):
    #TODO: use join() instead of events
    for word in sentence.split(' '):
        print(word, end=' ', flush=True)
        time.sleep(delay)
    if done_event:
        done_event.set()

def run():
    recorder = KeyedStreamingAudioRecorder(key='r', server_ip=WHISPER_HOST)
    recorder.standby(one_shot=False)
    parser = SentenceParser()
    sentence_thread = None

    while True:
        prompt = streaming_recorder.q.get()

        client = Client(GPT_HOST, GPT_PORT)
        client.send(prompt)

        token_seq = client.receive_stream()
        sentence_seq = parser.get_sentences(token_seq)

        for sentence in sentence_seq:
            if sentence_thread:
                sentence_thread.join()
            sentence_thread = Thread(target=typewrite, args=(sentence,))
            sentence_thread.start()
        sentence_thread.join()

        print(f"\n\n(token count: {len(parser.tokens)})")
        parser.reset()

