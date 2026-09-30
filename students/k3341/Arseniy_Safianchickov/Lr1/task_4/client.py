"""#4"""

import argparse
import socket
import threading


def receive_messages(reader) -> None:
    try:
        for line in reader:
            print(f"\r{line.rstrip()}\n> ", end="", flush=True)
    except (OSError, UnicodeError):
        pass
    print("\nDisconnected from chat.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multiplayer TCP chat client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9004)
    parser.add_argument("--name", help="Your name; prompted if omitted")
    args = parser.parse_args()

    name = args.name or input("Your name: ").strip()
    with socket.create_connection((args.host, args.port), timeout=5) as connection:
        connection.settimeout(None)
        connection.sendall((name + "\n").encode("utf-8"))
        # Read the login result before starting the background receiver.
        with connection.makefile("r", encoding="utf-8") as reader:
            greeting = reader.readline().rstrip()
            print(greeting)
            if not greeting.startswith("OK "):
                return

            threading.Thread(target=receive_messages, args=(reader,), daemon=True).start()
            try:
                while True:
                    message = input("> ")
                    connection.sendall((message + "\n").encode("utf-8"))
                    if message.strip() == "/quit":
                        break
            except (EOFError, KeyboardInterrupt):
                connection.sendall(b"/quit\n")
                print()


if __name__ == "__main__":
    main()
