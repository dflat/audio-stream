from client import Client
from audio_streaming import KeyedStreamingAudioRecorder
from config import WHISPER_HOST, GPT_HOST
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
   

def typewriter_print(sentence, done_event=None, delay=0.1):
    #TODO: use join() instead of events
    for word in sentence.split(' '):
        print(word, end=' ', flush=True)
        time.sleep(delay)
    if done_event:
        done_event.set()

def run():
    streaming_recorder = KeyedStreamingAudioRecorder(key='r',
                                                     server_ip=WHISPER_HOST)
    streaming_recorder.standby(one_shot=False)
    parser = SentenceParser()
    done = Event()
    done.set()
    while True:
        prompt = streaming_recorder.q.get()
        client = Client(GPT_HOST, 5000)
        client.send(prompt)
        token_seq = client.receive_stream()
        for token in token_seq:
            sentence = parser.feed(token.decode("utf-8"))
            if sentence is not None:
                done.wait()
                done.clear()
                Thread(target=typewriter_print, args=(sentence, done)).start()
        sentence = parser.end()
        done.wait()
        done.clear()
        Thread(target=typewriter_print, args=(sentence, done)).start()
        done.wait()
        print(f"\n(token count: {len(parser.tokens)})")
        parser.reset()

