import socket
from config import HOST, PORT, CHUNK_SIZE
from structures import Record

class Client:
    def __init__(self, host: str=HOST,
                       port: int=PORT,
                       chunk_size: int=CHUNK_SIZE):

        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self._connect()

    def _connect(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send(self, data: bytes) -> None:
        try:
            Record.send_over_socket(self.sock, data)
        except Exception as e:
            print(f"Client encountered error sending data: {e}")

    def receive(self) -> bytes:
        return Record.read_from_socket(self.sock)

    def end_transmission(self) -> None:
        Record.end_transmission(self.sock)

    def close(self) -> None:
        self.sock.close()