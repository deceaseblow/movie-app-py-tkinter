import socket
import threading

HOST = '127.0.0.1'
PORT = 5050
clients = []

def broadcast(msg, sender_sock):
    for client in clients:
        if client != sender_sock:
            try:
                client.send(msg)
            except:
                clients.remove(client)

def handle_client(conn):
    while True:
        try:
            msg = conn.recv(1024)
            if msg:
                broadcast(msg, conn)
            else:
                break
        except:
            break
    conn.close()
    clients.remove(conn)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Chat Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()
