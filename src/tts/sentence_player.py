from threading import Thread
from .audio_playback import fetch_and_play

def typewrite(sentence, delay=0.1):
    for word in sentence.split(' '):
        print(word, end=' ', flush=True)
        time.sleep(delay)

def play_and_type_text(sentence, type_transcript=True):
    if type_transcript:
        Thread(target=typewrite, args=(sentence,)).start()
    fetch_and_play(sentence)

class SentencePlayer:
    """
    Takes in an iterable of strings ("sentences"),
    and plays each back in succession as audio. 
    """
    def __init__(self):
        self.thread = None

    def play(self, sentence_seq):
        self.thread = None
        # Play each sentence in a thread. Wait until current sentence
        # completes playback before starting playback of next sentence.
        for sentence in sentence_seq:
            if self.thread:
                self.thread.join()
            self.thread = Thread(target=play_and_type_text, args=(sentence,))
            self.thread.start()
        self.thread.join()


