import tkinter as tk
from tkinter import messagebox
import threading
import socket

CHAT_HOST = '127.0.0.1'
CHAT_PORT = 5050

class ChatroomUI:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.room = "General"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((CHAT_HOST, CHAT_PORT))
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to chat server: {e}")
            return

        self.build_ui()

        # Start receiving messages in a new thread
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # Notify others this user joined
        self.send_raw_message(f"🔔 {self.username} joined the chat.")

    def build_ui(self):
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.chat_frame, text=f"💬 Chatroom: {self.room}", font=("Arial", 14, "bold")).pack(pady=10)

        self.text_area = tk.Text(self.chat_frame, state=tk.DISABLED, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        input_frame = tk.Frame(self.chat_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.entry = tk.Entry(input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        send_btn = tk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)

        back_btn = tk.Button(self.chat_frame, text="⬅ Back to Menu", command=self.on_back)
        back_btn.pack(pady=10)

    def send_message(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            full_msg = f"{self.username}: {msg}"
            try:
                self.sock.sendall(full_msg.encode())
            except:
                messagebox.showerror("Send Error", "Failed to send message.")
            self.entry.delete(0, tk.END)

    def send_raw_message(self, msg):
        """Send system messages like 'user joined'."""
        try:
            self.sock.sendall(msg.encode())
        except:
            pass

    def receive_messages(self):
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                if msg:
                    self.text_area.config(state=tk.NORMAL)
                    self.text_area.insert(tk.END, msg + "\n")
                    self.text_area.config(state=tk.DISABLED)
                    self.text_area.yview(tk.END)
                else:
                    break
            except:
                break

    def on_back(self):
        try:
            self.sock.sendall(f"🚪 {self.username} left the chat.".encode())
            self.sock.close()
        except:
            pass
        self.root.build_main_ui()
