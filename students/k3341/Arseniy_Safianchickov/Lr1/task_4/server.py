"""Multiplayer TCP chat. #4"""

from __future__ import annotations

import argparse
import socket
import threading


clients: dict[str, tuple[socket.socket, threading.Lock]] = {}
clients_lock = threading.Lock()


def send(connection: socket.socket, lock: threading.Lock, message: str) -> None:
    # Several client threads may send to the same socket concurrently.
    with lock:
        connection.sendall((message + "\n").encode("utf-8"))


def broadcast(message: str, exclude: str | None = None) -> None:
    with clients_lock:
        recipients = [(name, *client) for name, client in clients.items() if name != exclude]
    for _, connection, lock in recipients:
        try:
            send(connection, lock, message)
        except OSError:
            # The disconnected client's handler removes it from the registry.
            pass


def handle_client(connection: socket.socket, address: tuple[str, int]) -> None:
    name: str | None = None
    send_lock = threading.Lock()
    try:
        with connection:
            with connection.makefile("r", encoding="utf-8") as reader:
                proposed_name = reader.readline(256).strip()
                if not proposed_name or len(proposed_name) > 30 or ":" in proposed_name:
                    send(connection, send_lock, "ERROR Name must contain 1–30 characters and no colon")
                    return
                with clients_lock:
                    if proposed_name in clients:
                        accepted = False
                    else:
                        clients[proposed_name] = (connection, send_lock)
                        name = proposed_name
                        accepted = True
                if not accepted:
                    send(connection, send_lock, "ERROR This name is already in use")
                    return

                send(connection, send_lock, "OK Joined chat. Type /quit to leave.")
                print(f"{name} connected from {address}", flush=True)
                broadcast(f"* {name} joined the chat", exclude=name)
                for line in reader:
                    message = line.strip()
                    if message == "/quit":
                        break
                    if message:
                        print(f"{name}: {message}", flush=True)
                        broadcast(f"{name}: {message}", exclude=name)
    except (OSError, UnicodeError) as error:
        print(f"Connection {address} ended: {error}", flush=True)
    finally:
        if name is not None:
            with clients_lock:
                clients.pop(name, None)
            print(f"{name} left", flush=True)
            broadcast(f"* {name} left the chat")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multiplayer TCP chat server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9004)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen()
        print(f"Chat server listening on {args.host}:{args.port}", flush=True)
        while True:
            connection, address = server.accept()
            threading.Thread(target=handle_client, args=(connection, address), daemon=True).start()


if __name__ == "__main__":
    main()
