from .speech_to_text import SpeechToTextServer
from ..config import PORT

if __name__ == "__main__":
    server = SpeechToTextServer(host='', port=PORT)
    server.serve()
