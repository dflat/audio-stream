import socket
import threading
from config import PORT, CHUNK_SIZE
import teardown
from structures import Record

class Server:
    def __init__(self, host='', # Empty string to listen on all network interfaces.
                       port=PORT,
                       chunk_size=CHUNK_SIZE):

        teardown.register(self.teardown)
        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self._running = threading.Event()
        self.sentinel_message = b'x_end_x'
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid the error when restarting server by setting SO_REUSEADDR flag: 
        #   OSError: [Errno 48] Address already in use
        self.server_socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)

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
            sentinel_socket.sendall(self.sentinel_message)
        except Exception as e:
            print(f"Error sending shutdown sentinel: {e}")


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
                response = self._process_message(message)
                if response:
                    self._send(client_socket, response)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def _receive(self, client_socket):
        return Record.read_from_socket(client_socket)

    def _send(self, client_socket, response):
        """
        Override to do something different (e.g. save response 
        in _process_message and have _send be a no-op).
        """
        Record.send_over_socket(response)

    def _process_message(self, message):
        """
        Override in subclass to do something besides echo message back to client.
        """
        return message  # Echo the message back for now
