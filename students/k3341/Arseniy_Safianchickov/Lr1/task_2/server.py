"""TCP server. #2"""

import argparse
import json
import math
import socket


def calculate(request: dict) -> dict:
    try:
        a = float(request["a"])
        b = float(request["b"])
        if not math.isfinite(a) or not math.isfinite(b) or a <= 0 or b <= 0:
            raise ValueError("Both legs must be positive finite numbers")
        return {"hypotenuse": math.hypot(a, b)}
    except (KeyError, TypeError, ValueError) as error:
        return {"error": str(error)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pythagorean theorem TCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9002)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen()
        print(f"TCP server listening on {args.host}:{args.port}", flush=True)
        while True:
            connection, address = server.accept()
            with connection:
                with connection.makefile("r", encoding="utf-8") as reader:
                    line = reader.readline(4096)
                if not line:
                    continue
                try:
                    result = calculate(json.loads(line))
                except (json.JSONDecodeError, TypeError) as error:
                    result = {"error": f"Invalid request: {error}"}
                connection.sendall((json.dumps(result) + "\n").encode("utf-8"))
                print(f"{address}: {result}", flush=True)


if __name__ == "__main__":
    main()
