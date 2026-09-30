"""Small HTTP gradebook built directly on a TCP socket. #5"""

from __future__ import annotations

import argparse
import html
import json
import socket
from pathlib import Path
from urllib.parse import parse_qs


DATA_FILE = Path(__file__).with_name("grades.json")
MAX_HEADERS = 16_384
MAX_BODY = 65_536


def load_grades() -> dict[str, list[int]]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}


def save_grades(grades: dict[str, list[int]]) -> None:
    DATA_FILE.write_text(json.dumps(grades, ensure_ascii=False, indent=2), encoding="utf-8")


def render_page(grades: dict[str, list[int]]) -> bytes:
    rows = "".join(
        f"<tr><td>{html.escape(subject)}</td><td>{', '.join(map(str, values))}</td></tr>"
        for subject, values in sorted(grades.items())
    ) or '<tr><td colspan="2">Оценок пока нет</td></tr>'
    page = f"""<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><title>Журнал оценок</title></head>
<body>
  <h1>Журнал оценок</h1>
  <form method="post" action="/grades">
    <label>Дисциплина <input name="subject" required></label>
    <label>Оценка <input name="grade" type="number" min="2" max="5" required></label>
    <button type="submit">Добавить</button>
  </form>
  <table border="1">
    <thead><tr><th>Дисциплина</th><th>Все оценки</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""
    return page.encode("utf-8")


def response(status: str, body: bytes, extra_headers: str = "") -> bytes:
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"{extra_headers}"
        "Connection: close\r\n\r\n"
    )
    return headers.encode("ascii") + body


def read_request(connection: socket.socket) -> tuple[str, str, dict[str, str], bytes]:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = connection.recv(4096)
        if not chunk:
            raise ValueError("Incomplete HTTP headers")
        data += chunk
        if len(data) > MAX_HEADERS:
            raise ValueError("HTTP headers are too large")

    raw_headers, body = data.split(b"\r\n\r\n", 1)
    lines = raw_headers.decode("iso-8859-1").split("\r\n")
    method, path, version = lines[0].split(" ", 2)
    if not version.startswith("HTTP/"):
        raise ValueError("Invalid HTTP version")
    headers = {}
    for line in lines[1:]:
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError("Invalid HTTP header")
        headers[key.lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    if content_length < 0 or content_length > MAX_BODY:
        raise ValueError("Invalid Content-Length")
    while len(body) < content_length:
        chunk = connection.recv(min(4096, content_length - len(body)))
        if not chunk:
            raise ValueError("Incomplete HTTP body")
        body += chunk
    return method, path, headers, body[:content_length]


def handle_request(connection: socket.socket) -> None:
    try:
        method, path, headers, body = read_request(connection)
        if method == "GET" and path in ("/", "/grades"):
            result = response("200 OK", render_page(load_grades()))
        elif method == "POST" and path == "/grades":
            if headers.get("content-type", "").split(";", 1)[0] != "application/x-www-form-urlencoded":
                raise ValueError("Use application/x-www-form-urlencoded")
            fields = parse_qs(body.decode("utf-8"), keep_blank_values=True)
            subject = fields.get("subject", [""])[0].strip()
            grade_text = fields.get("grade", [""])[0]
            if not subject or len(subject) > 100:
                raise ValueError("Subject must contain 1–100 characters")
            if grade_text not in ("2", "3", "4", "5"):
                raise ValueError("Grade must be 2, 3, 4 or 5")
            grades = load_grades()
            grades.setdefault(subject, []).append(int(grade_text))
            save_grades(grades)
            result = response("303 See Other", b"", "Location: /\r\n")
        elif path not in ("/", "/grades"):
            result = response("404 Not Found", b"<h1>Not found</h1>")
        else:
            result = response("405 Method Not Allowed", b"<h1>Method not allowed</h1>")
    except (ValueError, UnicodeError) as error:
        result = response("400 Bad Request", f"<h1>Bad request</h1><p>{html.escape(str(error))}</p>".encode("utf-8"))
    connection.sendall(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Socket HTTP gradebook")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9005)
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
                    handle_request(connection)
                except socket.timeout:
                    pass


if __name__ == "__main__":
    main()
