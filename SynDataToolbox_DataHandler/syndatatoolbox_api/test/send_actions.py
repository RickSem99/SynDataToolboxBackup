import socket, struct
HOST='localhost'
PORT=9734
TIMEOUT=2.0
s=socket.socket()
s.settimeout(TIMEOUT)
try:
    s.connect((HOST,PORT))
    cmd = "ACTIONS".ljust(10).encode('utf-8')
    s.sendall(cmd)
    raw = s.recv(8192)
    print('RAW len:', len(raw))
    print('HEX:', raw.hex())
    if len(raw) >= 4:
        try:
            length = struct.unpack('<I', raw[:4])[0]
            payload = raw[4:4+length]
            print('Payload repr:', repr(payload.decode('utf-8', errors='replace')))
        except Exception:
            print('Decoded:', raw.decode('utf-8', errors='replace'))
    else:
        print('Decoded:', raw.decode('utf-8', errors='replace'))
except Exception as e:
    print('Error:', e)
finally:
    try:
        s.close()
    except:
        pass
