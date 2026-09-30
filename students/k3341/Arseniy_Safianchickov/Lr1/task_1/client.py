"""UDP client. #1"""

import argparse
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP greeting client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9001)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(5)
        client.sendto(b"Hello, server", (args.host, args.port))
        try:
            reply, _ = client.recvfrom(4096)
        except socket.timeout:
            print("No reply from server within 5 seconds")
            return
        print(reply.decode("utf-8"))


if __name__ == "__main__":
    main()
