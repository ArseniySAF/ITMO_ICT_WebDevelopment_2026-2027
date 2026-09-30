"""Serve index.html using a raw TCP socket. #3"""

import argparse
import socket
from pathlib import Path


PAGE = Path(__file__).with_name("index.html")


def response(status: str, body: bytes, content_type: str = "text/plain; charset=utf-8") -> bytes:
    headers = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers.encode("ascii") + body


def main() -> None:
    parser = argparse.ArgumentParser(description="Static socket HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9003)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen()
        print(f"Open http://{args.host}:{args.port}/", flush=True)
        while True:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(5)
                try:
                    request = connection.recv(4096).decode("iso-8859-1")
                    first_line = request.split("\r\n", 1)[0]
                    method, path, _ = first_line.split(" ", 2)
                    if method != "GET":
                        result = response("405 Method Not Allowed", b"Only GET is supported")
                    elif path not in ("/", "/index.html"):
                        result = response("404 Not Found", b"Not found")
                    else:
                        result = response("200 OK", PAGE.read_bytes(), "text/html; charset=utf-8")
                except (ValueError, socket.timeout):
                    result = response("400 Bad Request", b"Bad request")
                connection.sendall(result)


if __name__ == "__main__":
    main()
