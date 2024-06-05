from typing import Iterable
from io import BytesIO
import pyaudio
import requests
import numpy as np
import time
from collections import deque
import threading
import queue

from .text_to_speech import UnrealSpeech
from ..utils import buffer_to_array, save_wav

print('imports done')
WINDOW_SIZE = 2048

class MyBytesIO(BytesIO):
    def __len__(self):
        return WINDOW_SIZE

class StreamingAudioBuffer:
    wav_header_bytes = 78
    frames_per_window = 1024
    sample_width = 2
    window_size = frames_per_window * sample_width
    n_preload_frames = 16
    """
    UnrealSpeech streams audio that seems to start with:
        78 Byte Header
            1 - 4: RIFF (standard wav format lead-in)
            5 - 8: all ones (signalling start of header?)
            9 - 74? : unknown info
            75 - 78: all ones (signalling end of header?)
    """
    def __init__(self, response: requests.Response):
        self.response = response
        self.network_chunks = self.response.iter_content(self.window_size)

        # store window_size bytes in buffer to decouple from
        # network-streamed chunk size
        self.buffer = bytearray(self.window_size)
        self.buf_size = self.window_size
        self.buf_ix = 0
        self.buffer_view = memoryview(self.buffer)

        self.closed = False
        self.ix = 0

        self.window_queue = deque()
        self.preload()
        self.windows = self.window_generator()

    def flush_buffer(self):
        window = self.buffer_view.tobytes()
        self.window_queue.appendleft(window)
        self.buf_ix = 0

    def push_to_buffer(self, data):
        """
        Read data into self.buffer_view
        """
        data_size = len(data)
        dataview = memoryview(data)
        ix = 0
        while True:
            # calculate size of chunk to read
            buf_space_left = self.buf_size - self.buf_ix
            max_chunk_size = min(buf_space_left, data_size)
            chunk = dataview[ix:ix+max_chunk_size]
            chunk_size = len(chunk) # actual chunk size is bound by max_chunk_size

            # read chunk from data into buffer
            chunkview = dataview[ix:ix+chunk_size] 
            self.buffer_view[self.buf_ix:self.buf_ix+chunk_size] = chunkview 

            # update each index and check end / flush conditions
            ix += chunk_size
            self.buf_ix += chunk_size
            if self.buf_ix == self.buf_size:
                self.flush_buffer()
            if ix == data_size:
                break

    def get_chunk(self):
        try:
            return next(self.network_chunks)
        except StopIteration:
            return b''

    def preload(self):
        print('preload of window buffer starting...')
        # strip off wav header bytes from raw network byte stream
        first_chunk = self.get_chunk()
        data = first_chunk[self.wav_header_bytes:]
        self.push_to_buffer(data)
        # read chunks to build a network-latency-buffer
        for _ in range(self.n_preload_frames):
            self.push_to_buffer(self.get_chunk())
        print(f'preloaded {self.n_preload_frames} frame windows')

    def window_generator(self) -> Iterable[np.ndarray]:
        # stream bytes, but redirected through a window_queue
        while (chunk_bytes := self.get_chunk()):
            try:
                data = self.window_queue.pop() # queue has been pre-loaded
            except IndexError as e:
                print(f'unhandled error - stream too slow - {e}') 
                raise
            yield data
            self.push_to_buffer(chunk_bytes)

        # empty what remains in window queue (after stream ends)
        for _ in range(len(self.window_queue)):
            yield self.window_queue.pop()

    def process_window(self, buf: bytes) -> np.ndarray:
        # currently not being used (bytes are not being post-processed)
        arr = buffer_to_array(buf)
        arr = self._process(arr)
        return arr

    def _process(self, arr: np.ndarray) -> np.ndarray:
        # no op (could apply e.g. a gain smoothing curve/ramp)
        return arr

    def read(self, size=None) -> bytes:
        """
        Main public interface to get chunked audio data.
        """
        try:
            window = next(self.windows)
            return window
        except StopIteration:
            return b''  # EOF

    def close(self):
        self.response.close()
        self.closed = True

class StreamedAudioPlayer:
    """
    Plays back an audio_buffer, which is any
    object with a read() method that returns
    successive chunks of audio bytes. Specifically,
    works with StreamingAudioBuffer, which wraps
    a response object representing audio streamed
    over the network (e.g., from UnrealSpeech).
    """
    def __init__(self, audio_buffer):
        self.audio_buffer = audio_buffer
        self.paudio = pyaudio.PyAudio()
        self.stream = None
        self.window_size = WINDOW_SIZE # bytes per window

    def play(self):
        print('opening paudio stream...')
        stream = self.paudio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=22050,
                        output=True)
        print('paudio stream opened')

        n = self.window_size
        buf = self.audio_buffer

        while len(data := buf.read(n)):
            stream.write(data)

        stream.close()
        buf.close()

    def shutdown(self):
        # Release PortAudio system resources
        self.paudio.terminate()


def get_audio_buffer(text: str, stream=True, **kwargs):
    resp = UnrealSpeech.get_stream(text, **kwargs)
    if stream:
        # stream audio as it is being read from the network
        return StreamingAudioBuffer(resp)
    else: 
        # preload all audio data from network into memory
        by = b''.join(resp.iter_content(WINDOW_SIZE))
        #save_wav(by, 'test2.wav', frame_rate=22050) # for testing
        return BytesIO(by)

def fetch_and_play(text, stream=True):
    buf_stream = get_audio_buffer(text, stream)
    player = StreamedAudioPlayer(buf_stream)
    player.play()

def test_audio_playback_queue():
    """
    Test a playback queue to simulate an array
    of sentences converted into audio via
    a network service, and just upon completion,
    played as streamed audio, unless the last one
    is still playing: then wait for it to finish.
    Continue this until queue returns an 'end' sentinel.
    """
    def producer(q):
        sentences = ['this is a test',
                        'and this is another',
                        'and yet another test',
                        'end'
        ]
        for s in sentences:
            time.sleep(1) # simulate work being done (i.e., gpt token generation)
            q.put(s)

    def consumer(q):
        while True:
            sentence = q.get()
            if sentence == 'end':
                break
            fetch_and_play(sentence)

    q = queue.Queue()
    producer(q)
    consumer(q)