import socket
from config import HOST, PORT, CHUNK_SIZE

class Client:
    def __init__(self, host=HOST, port=PORT, chunk_size=CHUNK_SIZE):
        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send(self, data):
        try:
            self.client_socket.sendall(data)
        except Exception as e:
            print(f"Error sending data: {e}")

    def receive(self):
        response_chunks = []
        while True:
            chunk = self.client_socket.recv(self.chunk_size)
            if not chunk:
                break
            response_chunks.append(chunk)
        response = b''.join(response_chunks)
        return response

    def close(self):
        self.client_socket.close()

if __name__ == "__main__":
    # Example usage
    client = Client(HOST, PORT)
    
    # Simulating sending audio data (as bytes)
    audio_data = b'This is a simulated audio byte stream'
    client.send(audio_data)
    
    # Receiving the response
    response = client.receive()
    print(f"Received response: {response}")
    
    # Closing the connection
    client.close()
