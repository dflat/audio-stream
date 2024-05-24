import socket
import threading
from config import PORT, CHUNK_SIZE

class Server:
    def __init__(self, host='', # Empty string to listen on all network interfaces.
                       port=PORT,
                       chunk_size=CHUNK_SIZE):
        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self._running = threading.Event()
        self.sentinel_message = b'x_end_x'
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Listen for up to 5 connections

    @property
    def running(self):
        return self._running.is_set()

    def serve(self):
        print(f"Server is listening on {self.host}:{self.port}")
        self._running.set()
        threading.Thread(target=self._serve).start()

    def shutdown(self):
        self._running.clear()
        sentinel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sentinel_socket.connect(('localhost', self.port))
            sentinel_socket.sendall(self.sentinel_message)
        except Exception as e:
            print(f"Error sending shutdown sentinel: {e}")


    def _serve(self):
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
        print('Server has been shut down.')

    def handle_client(self, client_socket):
        try:
            message = self.receive(client_socket)
            if message:
                print(f"Received message of length: {len(message)} bytes")
                if message == self.sentinel_message:
                    print('Server got sentinel shutdown signal.')
                    return client_socket.close()
                response = self.process_message(message)
                if response:
                    self.send(client_socket, response)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def receive(self, client_socket):
        chunks = []
        while True:
            chunk = client_socket.recv(self.chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks)

    def send(self, client_socket, response):
        """
        Override to do something different (e.g. save response 
        in process_message and have send be a no-op).
        """
        client_socket.sendall(response)

    def process_message(self, message):
        """
        Override in subclass to do something besides echo message back to client.
        """
        return message  # Echo the message back for now

class SpeechToTextServer(Server):
    def __init__(self, host='', port=PORT, chunk_size=CHUNK_SIZE):
        super().__init__(host, port, chunk_size)

    def speech_to_text(self, buffer):
        print('converting speech to text...')
        self.buffer = buffer
        # call whisper here...TODO
        # trancript = whisper(...)
        # return transcript

    def process_message(self, message):
        """
        Message will be a bytestring (buffer) streamed by client
        (perhaps via live microphone recording).
        """
        transcript = self.speech_to_text(message)

if __name__ == "__main__":
    server = SpeechToTextServer(host='127.0.0.1', port=5000)
    server.serve()
