import pyaudio
import wave
import time
import socket
import threading
from config import PORT, AUDIO_SAMPLE_RATE, CHANNELS, AUDIO_CHUNK_SIZE, WHISPER_HOST
from pydub import AudioSegment
from key_input import KeyboardListener
from structures import Record

class BaseAudioRecorder:
    """
    Base class for LocalAudioRecorder and StreamingAudioRecorder.
    Main methods to override are _init() _start(), _handle_data(), and _stop().
    (See these methods on this class for more detail).
    The main engine of recording is done in _record().
    The public api to use the class consists of the record() and stop() methods.
    """
    def __init__(self, rate=AUDIO_SAMPLE_RATE, channels=CHANNELS, chunk=AUDIO_CHUNK_SIZE):
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.width = self.audio.get_sample_size(self.format)
        self.poll_delay = 0.01

    def record(self):
        """
        Public api method to start recording. Records in a new thread.
        """
        if not self.recording:
            self._init()
            threading.Thread(target=self._record).start()
            print('Recording started...')
        else:
            print('Recording already in progress.')

    def stop(self):
        """
        Public api method to stop recording.
        """
        if self.recording:
            self.recording = False
            print('Stop-recording request submitted...')
        else:
            print('Recording has not started: call to stop() ignored.')

    def start_stream(self):
        """
        Initializes microphone input capture for recording.
        """
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)

    def stop_stream(self):
        """
        Ends microphone input capture.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        print('Stopped recording.')

    def _init(self):
        """
        Called before main record thread launches. Setup
        any necessary data structrues for recording.
        Override for custom behavior.
        """
        self.frames = []

    def _start(self):
        """
        Called in record thread, just before main record loop begins.
        Override for custom behavior.
        """
        self.recording = True
        self.start_stream()

    def _stop(self):
        """
        Called in record thread, just after main record loop ends,
        either via an exception, or a user call to stop().
        Override for custom behavior.
        """
        self.stop_stream()

    def _handle_data(self, data):
        """
        Called repeatedly in record thread loop,
        after each chunk of audio data is read.
        Override for custom behavior.
        """
        self.frames.append(data)

    def _record(self):
        """
        Main record loop. Starts in new thread, triggered by call to record().
        """
        self._start()
        try:        
            while self.recording:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self._handle_data(data)
                except IOError as e:
                    print(f"Error: {e}")
                time.sleep(self.poll_delay)
        except KeyboardInterrupt:
            print("Recording interrupted.")
        finally:
            self._stop()

class LocalAudioRecorder(BaseAudioRecorder):
    """
    Record audio from microphone and save to disk as wav/mp3.
    """
    def __init__(self, filename="test",
                        rate=AUDIO_SAMPLE_RATE,
                        channels=CHANNELS,
                        chunk=AUDIO_CHUNK_SIZE):

        super().__init__(rate, channels, chunk)
        self.basename = self.get_basename(filename)
        self.wav_path = self.basename + '.wav'
        self.mp3_path = self.basename + '.mp3'

    def get_basename(self, filename):
        return filename.rsplit('.', maxsplit=1)[0] # remove any suffix

    def _stop(self):
        """
        Extends BaseAudioRecorder._stop()
        """
        super()._stop()
        self.save_wav()
        self.convert_to_mp3()

    def save_wav(self):
        wf = wave.open(self.wav_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.width)
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

    def convert_to_mp3(self):
        audio_segment = AudioSegment.from_wav(self.wav_path)
        audio_segment.export(self.mp3_path, format="mp3")

    def record_and_save(self, filename, duration):
        """
        Conveinence function to test recording behavior.
        """
        print(f'Recording for {duration} seconds...')
        self.basename = self.get_basename(filename)
        self.record()
        time.sleep(duration)
        self.stop()
        print(f"Recording saved as: {self.wav_path}, {self.mp3_path}")

class StreamingAudioRecorder(BaseAudioRecorder):
    """
    Record audio from microphone and stream over network socket.
    """
    def __init__(self, rate=AUDIO_SAMPLE_RATE,
                        channels=CHANNELS,
                        chunk=AUDIO_CHUNK_SIZE,
                        server_ip='127.0.0.1',
                        server_port=PORT):

        super().__init__(rate, channels, chunk)
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.waiting_for_response = False

    def open_socket(self):
        """
        Creates a TCP Socket to stream audio data over a network,
        incrementally, as it is recorded from a microphone input source.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))

    def close_socket(self):
        self.socket.close()

    ### The below four methods ovverride BaseAudioRecorder methods: 
    ##      _init, _start, _handle_data, _stop
    
    def record(self):
        if self.waiting_for_response:
            return print('Transcribing...ignoring request to record.')
        super().record()

    def _init(self):
        self.open_socket()

    def _start(self):
        super()._start()

    def _handle_data(self, data):
        #self.socket.sendall(data)
        Record.send_over_socket(self.socket, data)

    def _stop(self):
        super()._stop()
        Record.end_transmission(self.socket)
        self._receive_response()
        #self.close_socket()

    def _receive_response(self):
        self.waiting_for_response = True
        self.response = Record.read_from_socket(self.socket)
        self.waiting_for_response = False
        print('\nGot:', self.response.decode('utf-8'))
   
    ##
    ### END Overridden BaseAudioRecorder methods.


class KeyedStreamingAudioRecorder(StreamingAudioRecorder):
    """
    StreamingAudioRecorder, but microphone recording is
      triggered with keypress event.
    """
    def __init__(self, key,
                        rate=AUDIO_SAMPLE_RATE,
                        channels=CHANNELS,
                        chunk=AUDIO_CHUNK_SIZE,
                        server_ip='127.0.0.1',
                        server_port=PORT):

        super().__init__(rate, channels, chunk, server_ip, server_port)
        self.key = key
        self.keyboard = KeyboardListener(key=self.key,
                                         start_callback=self.record,
                                         end_callback=self.stop,
                                         one_shot=False)

    def standby(self, one_shot=False):
        """
        If one_shot is set to True, Call every time you want to wait 
            for a keypress. Upon key up event of self.key, keyboard listener
            is shutdown until standby() is called again.
        If one_shot is set to False, contniually listen for keypress,
            without the need to re-invoke standby().
        """
        print(f"Press and hold the '{self.key}' key to start streaming audio...")
        self.keyboard.one_shot = one_shot
        self.keyboard.listen()

    def stop_listening(self):
        self.keyboard.stop_listening()

if __name__ == "__main__":
    # Example usage for recording and saving to MP3
    #local_recorder = LocalAudioRecorder()
    #local_recorder.record_and_save("test_audio", duration=5)

    # Example usage for streaming audio
    streaming_recorder = KeyedStreamingAudioRecorder(key='r',
                                                     server_ip=WHISPER_HOST)
    streaming_recorder.standby(one_shot=False)
