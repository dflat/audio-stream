import time
from config import PORT, CHUNK_SIZE
from server import MessageInSequenceOutServer
from gpt4all import GPT4All
from model_config import SYSTEM_PROMPT
from typing import Generator


class GPT:
    settings = dict(temp = 0.7, 
                    top_k = 40, 
                    top_p = 0.4, 
                    min_p = 0, 
                    repeat_penalty = 1.18, 
                    n_batch = 16, 
                    max_tokens = 400, 
                    streaming = True)

    def __init__(self,
                model_name="Meta-Llama-3-8B-Instruct.Q4_0.gguf", 
                context_size=4096):
        self.model_name = model_name
        self.context_size = context_size
        self.load_model()
        self.start_session()


    def load_model(self):
        print("loading model")
        self.model = GPT4All(model_name=self.model_name,
                            n_ctx=self.context_size)
        print("finished loading model")

    def start_session(self):
        self.gen = self.start()
        next(self.gen)

    def start(self):
        with self.model.chat_session(SYSTEM_PROMPT) as session:
            print("chat session loaded")
            self.ping_model()
            yield

    def ping_model(self):
        print("pinging model")
        start = time.time()
        self.model.generate(prompt = "ping")
        end = time.time()
        print(f"finished pinging {end-start:.1f} seconds")

    def get_tokens(self, prompt):
        yield from self.model.generate(prompt = prompt, **self.settings)

    def end_session(self):
        next(self.gen)

class GPTServer(MessageInSequenceOutServer):
	def __init__(self, host='',
                       port=PORT,
                       chunk_size=CHUNK_SIZE,):

        super().__init__(host='', port=PORT, chunk_size=CHUNK_SIZE)
        self.gpt = GPT()
        
    def _process(self, message: bytes) -> Generator[bytes, None, None]:
    	return (token.encode('utf-8') for token in self.gpt.get_tokens(message))
