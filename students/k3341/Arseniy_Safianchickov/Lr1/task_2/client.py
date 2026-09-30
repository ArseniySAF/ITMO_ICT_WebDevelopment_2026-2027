"""TCP client. #2"""

import argparse
import json
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description="Pythagorean theorem TCP client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9002)
    args = parser.parse_args()

    a = input("First leg a: ")
    b = input("Second leg b: ")
    with socket.create_connection((args.host, args.port), timeout=5) as client:
        client.sendall((json.dumps({"a": a, "b": b}) + "\n").encode("utf-8"))
        with client.makefile("r", encoding="utf-8") as reader:
            response = json.loads(reader.readline())

    if "error" in response:
        print(f"Error: {response['error']}")
    else:
        print(f"Hypotenuse: {response['hypotenuse']:g}")


if __name__ == "__main__":
    main()
