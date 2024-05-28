"""
Servers come in four varieties:
    MIMO (Message In Message Out)   : message input  -> message response
    MISO (Message In Sequence Out)  : message input  -> streamed response
    SIMO (Sequence In Message Out)  : streamed input -> message response
    SISO (Sequence In Sequence Out) : steramed input -> streamed response

    The normal server class, Server, is MIMO. The other varieties are
    subclasses of Server, found below.
"""
from typing import Generator
import socket
import threading
from ..utils import teardown
from ..config import PORT, CHUNK_SIZE
from .structures import Transmit

class Server:
    """
    Message In Message Out server. (Normal Server)

    Example Use Case:
        client sends a text request ->
        returns a text response, and ends the connection.
    """
    def __init__(self, host='', # Empty string to listen on all network interfaces.
                       port=PORT,
                       chunk_size=CHUNK_SIZE):

        teardown.register(self.teardown)
        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self.keep_alive = False # maybe make True
        self._running = threading.Event()
        self.sentinel_message = b'x_end_x'
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid the error when restarting server by setting SO_REUSEADDR flag: 
        #   OSError: [Errno 48] Address already in use
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Listen for up to 5 connections

    @property
    def running(self):
        return self._running.is_set()

    def serve(self):
        print(f"\nServer is listening on {self.host}:{self.port}")
        self._running.set()
        threading.Thread(target=self._serve).start()

    def teardown(self):
        if self.running:
            print('Dirty exit: fallback teardown started...')
            self.shutdown()

    def shutdown(self):
        self._running.clear()
        sentinel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sentinel_socket.connect(('localhost', self.port))
            self._send(sentinel_socket, self.sentinel_message)
            #sentinel_socket.sendall(self.sentinel_message)
        except Exception as e:
            print(f"Error sending shutdown sentinel: {e}")
            raise

    def _serve(self):
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            client_thread.start()
        print('Server has been shut down.')

    def _handle_client(self, client_socket):
        try:
            message = self._receive(client_socket)
            if message:
                print(f"Received message of length: {len(message)} bytes")
                if message == self.sentinel_message:
                    print('Server got sentinel shutdown signal.')
                    return client_socket.close()

                message = self._process(message)
                self._send(client_socket, message)
            else:
                print('Message was nullish value')

        except Exception as e:
            print(f"Error handling client: {e}")
            client_socket.close() 
            raise

        finally:
            if not self.keep_alive:
                client_socket.close() # maybe don't close on server

    def _process(self, message):
        return message

    def _receive(self, client_socket):
        return Transmit.read_from_socket(client_socket)

    def _send(self, client_socket, response):
        Transmit.send_over_socket(client_socket, response)

class MessageInSequenceOutServer(Server):
    """
    Example Use Case:
        Receive as input a text prompt, and run through a GPT,
        respond with a stream of GPT-generated tokens.
    """
    def _process(self, message: bytes) -> Generator[bytes, None, None]:
        raise NotImplementedError()

    def _send(self, client_socket, sequence: Generator[bytes, None, None]) -> None:
        for message in sequence:
            super()._send(client_socket, message)
        Transmit.end_transmission(client_socket)


class SequenceInMessageOutServer(Server):
    """
    Example Use Case:
        Receive as input an audio stream (e.g., from microphone capture),
        and run a speech-to-text conversion -> return text transcript response.
    """
    def _receive(self, client_socket):
        """
        Receive stream chunks in a loop until end of transmission signal.
        """
        chunks = []
        while True:
            chunk = super()._receive(client_socket)
            if chunk is None: # got end of transmission
                return b''.join(chunks)
            chunks.append(chunk)

class SequenceInSequenceOutServer(Server):
    pass
