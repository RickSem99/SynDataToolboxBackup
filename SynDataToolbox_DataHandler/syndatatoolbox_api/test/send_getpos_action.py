import socket
import struct

HOST = 'localhost'
PORT = 9734

def recv_n(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            break
        data.extend(packet)
    return bytes(data)

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    try:
        # The action protocol expects a trailing underscore for the action terminator
        cmd = 'ACTION_CoordinateActionManager(CoordinateActionManagerSDT)_GETPOS_'
        # Pad to 1000 bytes as IsarSocket does
        cmd_padded = cmd.ljust(1000)[:1000]
        s.sendall(cmd_padded.encode('utf-8'))

        raw = recv_n(s, 4)
        if len(raw) < 4:
            print('No length prefix received')
            return
        length = struct.unpack('<I', raw)[0]
        payload = recv_n(s, length)
        print('GETPOS payload repr:', repr(payload.decode('utf-8', errors='replace')))
        print('GETPOS payload hex:', ' '.join(f"{b:02x}" for b in payload))

    except Exception as e:
        print('Error:', e)
    finally:
        s.close()

if __name__ == '__main__':
    main()
