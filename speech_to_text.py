from server import Server
import numpy as np
from config import PORT, CHUNK_SIZE, WHISPER_MODEL
import queue

class Whisper:
    def __init__(self, model_name=WHISPER_MODEL):
        self.loaded = False
        self._init_model(model_name)

    def _init_model(self, model_name):
        import whisper
        console.load('whisper model loading.')
        self.model = whisper.load_model(model_name)
        console.load('whisper model loaded.')
        self.loaded = True

    def transcribe(self, audio_data):
        print('converting speech to text...')
        self.result = self.model.transcribe(audio_data)
        return self.result['text']

class SpeechToTextServer(Server):
    def __init__(self, model_name=WHISPER_MODEL,
                        host='',
                        port=PORT,
                        chunk_size=CHUNK_SIZE):

        super().__init__(host, port, chunk_size)
        self.stt_model = Whisper(model_name)

    def sequential_send(self, sequence):
        for token in sequence:
            pass

    def speech_to_text(self, audio_array):
        transcript = self.stt_model.transcribe(audio_array)
        return transcript

    def _process_message(self, message):
        """
        Message will be a bytestring (buffer) streamed by client
        (perhaps via live microphone recording).
        """
        audio_array = normalize(buffer_to_array(message))
        transcript = self.speech_to_text(audio_array)
        return transcript

class QueuedSpeechToTextServer(SpeechToTextServer):
    def __init__(self, q=None,
                        host='',
                        port=PORT,
                        chunk_size=CHUNK_SIZE):

        super().__init__(host=host, port=port, chunk_size=chunk_size)
        self.q = q or queue.Queue()

    def _send(self, client_socket, response):
        """
        Override normal response-sending behavior of the server.
        Instead of sending a response to client_socket, push
        the response (the transcribed text) onto a queue,
        for further processing (e.g., by a GPT).
        """
        self.q.put(response)

def buffer_to_array(buffer, dtype=np.int16):
    return np.frombuffer(buffer, dtype=dtype) 

def normalize(arr):
    return arr.astype(np.float32) / np.iinfo(np.int16).max

if __name__ == "__main__":
    q = queue.Queue()
    server = QueuedSpeechToTextServer(q=q, host='127.0.0.1',
                                            port=PORT)
    server.serve()

