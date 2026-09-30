"""Run end-to-end checks for all five socket exercises on localhost."""

import json
import shutil
import socket
import subprocess
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def free_port() -> int:
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


def start(script: Path, port: int) -> subprocess.Popen:
    process = subprocess.Popen(
        ["python3", "-B", str(script), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout.readline(), process.stderr.read()
    return process


def stop(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()


def check_udp() -> None:
    port = free_port()
    server = start(ROOT / "task_1/server.py", port)
    try:
        output = subprocess.check_output(
            ["python3", "-B", str(ROOT / "task_1/client.py"), "--port", str(port)],
            text=True,
        )
        assert "Hello, client" in output
    finally:
        stop(server)
    print("Task 1 UDP: OK")


def check_pythagoras() -> None:
    port = free_port()
    server = start(ROOT / "task_2/server.py", port)
    try:
        output = subprocess.check_output(
            ["python3", "-B", str(ROOT / "task_2/client.py"), "--port", str(port)],
            input="3\n4\n",
            text=True,
        )
        assert "Hypotenuse: 5" in output, output
        with socket.create_connection(("127.0.0.1", port)) as connection:
            connection.sendall(b'{"a": -3, "b": 4}\n')
            assert "error" in connection.recv(4096).decode()
    finally:
        stop(server)
    print("Task 2 Pythagoras: OK")


def check_static_http() -> None:
    port = free_port()
    server = start(ROOT / "task_3/server.py", port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as reply:
            body = reply.read()
            assert reply.status == 200
            assert len(body) == int(reply.headers["Content-Length"])
            assert b"index.html" in body
    finally:
        stop(server)
    print("Task 3 HTTP page: OK")


def check_chat() -> None:
    port = free_port()
    server = start(ROOT / "task_4/server.py", port)
    alice = bob = charlie = None
    try:
        alice = socket.create_connection(("127.0.0.1", port))
        alice.settimeout(2)
        alice_reader = alice.makefile("r", encoding="utf-8")
        alice.sendall(b"Alice\n")
        assert alice_reader.readline().startswith("OK")

        bob = socket.create_connection(("127.0.0.1", port))
        bob.settimeout(2)
        bob_reader = bob.makefile("r", encoding="utf-8")
        bob.sendall(b"Bob\n")
        assert bob_reader.readline().startswith("OK")
        assert "Bob joined" in alice_reader.readline()

        charlie = socket.create_connection(("127.0.0.1", port))
        charlie.settimeout(2)
        charlie_reader = charlie.makefile("r", encoding="utf-8")
        charlie.sendall(b"Charlie\n")
        assert charlie_reader.readline().startswith("OK")
        assert "Charlie joined" in alice_reader.readline()
        assert "Charlie joined" in bob_reader.readline()
        charlie.sendall(b"Hello everyone\n")
        assert "Charlie: Hello everyone" in alice_reader.readline()
        assert "Charlie: Hello everyone" in bob_reader.readline()

        bob.sendall(b"Hello Alice\n")
        assert "Bob: Hello Alice" in alice_reader.readline()
        assert "Bob: Hello Alice" in charlie_reader.readline()
        bob.sendall(b"/quit\n")
        assert "Bob left" in alice_reader.readline()
        assert "Bob left" in charlie_reader.readline()
        alice.sendall(b"/quit\n")
        charlie.sendall(b"/quit\n")
    finally:
        if alice is not None:
            alice.close()
        if bob is not None:
            bob.close()
        if charlie is not None:
            charlie.close()
        stop(server)
    print("Task 4 chat: OK")


def check_gradebook() -> None:
    # Run a copy so the test does not change the student's real grade data.
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / "server.py"
        shutil.copyfile(ROOT / "task_5/server.py", script)
        port = free_port()
        server = start(script, port)
        try:
            url = f"http://127.0.0.1:{port}/grades"
            for grade in (4, 5):
                request = urllib.request.Request(
                    url,
                    data=f"subject=Mathematics&grade={grade}".encode(),
                    method="POST",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                with urllib.request.urlopen(request) as reply:
                    assert reply.status == 200
            with urllib.request.urlopen(url) as reply:
                page = reply.read().decode()
                assert page.count("Mathematics") == 1
                assert "4, 5" in page
            grades = json.loads((Path(directory) / "grades.json").read_text())
            assert grades == {"Mathematics": [4, 5]}
        finally:
            stop(server)
    print("Task 5 gradebook: OK")


if __name__ == "__main__":
    check_udp()
    check_pythagoras()
    check_static_http()
    check_chat()
    check_gradebook()
