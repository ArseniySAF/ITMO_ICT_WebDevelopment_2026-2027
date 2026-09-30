"""UDP server. #1"""

import argparse
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP greeting server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9001)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((args.host, args.port))
        print(f"UDP server listening on {args.host}:{args.port}", flush=True)
        message, client_address = server.recvfrom(4096)
        print(f"From {client_address}: {message.decode('utf-8')}", flush=True)
        server.sendto("Hello, client".encode("utf-8"), client_address)


if __name__ == "__main__":
    main()
