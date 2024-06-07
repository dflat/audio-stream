from .config import WHISPER_HOST, GPT_HOST, GPT_PORT
from .network import Client
from .audio_streaming import KeyedStreamingAudioRecorder
from .utils import SentenceParser
from .tts import SentencePlayer

def run():
    recorder = KeyedStreamingAudioRecorder(key='r', server_ip=WHISPER_HOST)
    parser = SentenceParser()
    player = SentencePlayer()

    recorder.standby(one_shot=False)

    # Main prompt -> response loop, driven by user speech input.
    while True:
        # (1) Convert microphone-captured speech to text.
        prompt = recorder.wait_for_input() 

        # (2) Send prompt to GPT server, await response.
        client = Client(GPT_HOST, GPT_PORT)
        client.send(prompt) 

        # (3) Receive response tokens as GPT server produces them.
        token_seq = client.receive_stream() 

        # (4) Collate tokens into sentences as they are emitted.
        sentence_seq = parser.get_sentences(token_seq)

        # (5) Convert sentences to audio, and play each back in sequence.
        #       Blocks until all sentences finish playing
        player.play(sentence_seq) 

        # (6) Print number of tokens used in the response.
        print(f"\n\n(token count: {parser.n_tokens})")

