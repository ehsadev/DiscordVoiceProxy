import socket


def is_socks5(host: str, port: int, timeout: float = 0.18) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(b"\x05\x01\x00")
            reply = s.recv(2)
            return len(reply) == 2 and reply[0] == 5 and reply[1] in (0, 1, 2, 255)
    except (OSError, TimeoutError):
        return False
