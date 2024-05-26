import struct
import socket
import math
from typing import Union

class Record:
    """
    Static class, providing an interface for streaming chunks of variable
        size over the network. Uses an end_of_transmission signal.

    Main public API usage:
        Given a socket object, (sock), and some bytes (payload):
            Record.send_over_socket(sock, payload) 
            payload = Record.read_from_socket(sock)
        When read_from_socket returns None, transmission is complete.
    """
    size_prefix_type = '!I'  # 32-bit unsigned integer, big-endian
    prefix_size = struct.calcsize(size_prefix_type)
    end_of_transmission = 2**32 - 1

    @classmethod
    def send_over_socket(cls, sock: socket.socket, payload: bytes):
        sock.sendall(cls._prepend_size(payload))

    @classmethod
    def read_from_socket(cls, sock: socket.socket) -> Union[bytes, None]:
        try:
            size_bytes = sock.recv(cls.prefix_size)

            if len(size_bytes) < 4:
                raise ConnectionError("Incomplete size data received")

            size = cls._read_size(size_bytes)
            if size == cls.end_of_transmission:
                return None

            payload = cls._receive(sock, size)

            return payload

        except Exception as e:
            print(f"Error: {e}")
            sock.close()
            print('socket closed by exception in Record.read_from_socket')
            raise

    @classmethod
    def end_transmission(cls, sock: socket.socket):
        sentinel = struct.pack(cls.size_prefix_type, cls.end_of_transmission)
        cls.send_over_socket(sock, sentinel) 

    @classmethod
    def _receive(cls, sock: socket.socket, size: int):
        """
        Read arg::size bytes from arg::sock to receive complete payload.
        """
        chunks = []
        bytes_read = 0

        while bytes_read < size:
            bytes_remaining = size - bytes_read
            if bytes_remaining == 0:
                break

            chunk = sock.recv(min(4096, bytes_remaining))
            if not chunk:
                raise ConnectionError("Connection closed before receiving full payload")

            bytes_read += len(chunk)
            chunks.append(chunk)

        return b''.join(chunks) 

    @classmethod
    def _read_size(cls, size_prefix: bytes) -> int:
        """
        Use just after receiving (4) bytes from network socket.
        (4 is assuming size_prefix_type is an unsigned int (e.g., !I or I)).
        """
        return struct.unpack(cls.size_prefix_type, size_prefix)[0]

    @classmethod
    def _prepend_size(cls, payload: bytes) -> bytes:
        """
        Use prior to sending over network socket.
        Return the payoad with its size (in number of bytes) prepended.
        """
        return struct.pack(cls.size_prefix_type, len(payload)) + payload
        
