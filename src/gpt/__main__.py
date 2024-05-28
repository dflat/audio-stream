from .gpt import GPTServer

if __name__ == '__main__':
    gpt = GPTServer()
    gpt.serve()
