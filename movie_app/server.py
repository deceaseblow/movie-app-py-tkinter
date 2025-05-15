import socket
import threading
from client_handler import handle_client

HOST = '127.0.0.1'
PORT = 5000

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"[CONNECTION] Accepted from {addr}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()
