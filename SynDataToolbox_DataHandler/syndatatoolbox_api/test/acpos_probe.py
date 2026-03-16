import socket, struct, time

HOST = 'localhost'
PORT = 9734
TIMEOUT = 2.0


def probe(command_bytes):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TIMEOUT)
        s.connect((HOST, PORT))
        s.sendall(command_bytes)
        time.sleep(0.05)
        try:
            raw = s.recv(8192)
        except socket.timeout:
            raw = b''
    return raw


def inspect(raw):
    print("RAW length:", len(raw))
    print("HEX:", raw.hex())
    try:
        print("REPR:", repr(raw.decode('utf-8', errors='replace')))
    except Exception as e:
        print("Decoding error:", e)

    if len(raw) >= 4:
        try:
            length = struct.unpack('<I', raw[:4])[0]
            print("Detected 4-byte length prefix (LE):", length)
            payload = raw[4:4+length]
            print("Payload hex:", payload.hex())
            try:
                print("Payload repr:", repr(payload.decode('utf-8', errors='replace')))
            except Exception:
                pass
        except struct.error:
            pass

    # prova a estrarre numeri separati da virgola
    try:
        s = raw.decode('utf-8', errors='ignore').replace('\x00','').strip()
    except Exception:
        s = ''
    if s:
        print('Decoded text (clean):', s)
    if ',' in s:
        parts = [p.strip() for p in s.split(',') if p.strip()!='']
        print('Parts:', parts)
        try:
            nums = [float(p) for p in parts]
            print('Parsed floats:', nums)
        except Exception as e:
            print('Parsing floats failed:', e)


if __name__ == '__main__':
    cmds = [
        ("ACPOS ljust(10)", "ACPOS".ljust(10).encode('utf-8')),
        ("ACPOS raw", b"ACPOS"),
        ("ACPOS newline", b"ACPOS\n"),
    ]
    for name, cmd in cmds:
        print('\n--- Sending:', name)
        try:
            raw = probe(cmd)
            inspect(raw)
        except Exception as e:
            print('Errore connessione/invio:', e)
