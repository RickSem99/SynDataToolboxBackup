import socket
import time

HOST = 'localhost'
PORT = 9734

variants = [
    "ACPOS",
    "ACPOS\n",
    "ACPOS\x00",
    "ACPOS".ljust(10),
    "ACPOS".ljust(1000),
]


def show_bytes(b: bytes) -> str:
    return ' '.join(f"{x:02x}" for x in b[:128]) + (" ..." if len(b) > 128 else "")


def main():
    print(f"Connecting to {HOST}:{PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    for v in variants:
        try:
            print("\n--- Sending variant repr: ", repr(v))
            s.sendall(v.encode('utf-8'))
            time.sleep(0.1)
            try:
                data = s.recv(4096)
            except socket.timeout:
                print("No response (timeout)")
                continue
            if not data:
                print("Empty response")
                continue
            try:
                decoded = data.decode('utf-8', errors='replace')
            except Exception:
                decoded = '<unable to decode>'
            print("Response repr:", repr(decoded))
            print("Response hex:", show_bytes(data))
        except Exception as e:
            print(f"Error while sending/receiving: {e}")

    s.close()


if __name__ == '__main__':
    main()
