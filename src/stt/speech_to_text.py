print('importing numpy...', end=' ')
import numpy as np
print('loaded.')
import queue
import threading
from ..config import PORT, CHUNK_SIZE, WHISPER_MODEL
from ..network import SequenceInMessageOutServer
from ..utils import save_wav, buffer_to_array, normalize

class Whisper:
    def __init__(self, model_name=WHISPER_MODEL):
        self.loaded = False
        self._init_model(model_name)

    def _init_model(self, model_name):
        print('importing whisper...', end=' ')
        import whisper
        print('loaded.')
        print('whisper model loading...', end=' ')
        self.model = whisper.load_model(model_name)
        print('loaded.')
        self.loaded = True

    def transcribe(self, audio_data):
        print('converting speech to text...')
        self.result = self.model.transcribe(audio_data,
                                            fp16=False,
                                            language='en')
        return self.result['text']

class SpeechToTextServer(SequenceInMessageOutServer):
    def __init__(self, model_name=WHISPER_MODEL,
                        host='',
                        port=PORT,
                        chunk_size=CHUNK_SIZE):

        super().__init__(host, port, chunk_size)
        self.stt = Whisper(model_name)

    def speech_to_text(self, audio_array):
        transcript = self.stt.transcribe(audio_array)
        return transcript

    def _process(self, message: bytes) -> bytes:
        """
        Message will be a completed bytes object (buffer),
        streamed by client (perhaps via live microphone recording).
        """
        print('saving wav file...', end=' ')
        save_wav(message, 'test_1ch_16000hz.wav')
        print('saved.')

        audio_array = normalize(buffer_to_array(message))
        transcript = self.speech_to_text(audio_array)
        return transcript.encode('utf-8')

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


def continuous_transcribe():
    while server.running:
        try:
            print('waiting for speech transmission...')
            transcript = q.get()
            print('Got:', transcript)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    #q = queue.Queue()
    #server = QueuedSpeechToTextServer(q=q, host='',
    #                                        port=PORT)
    #server.serve()
    #continuous_transcribe()
    server = SpeechToTextServer(host='', port=PORT)
    server.serve()


