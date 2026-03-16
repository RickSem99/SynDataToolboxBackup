import socket, struct, time
HOST='localhost'
PORT=9734
TIMEOUT=2.0

def send_and_recv(cmd_bytes):
    s=socket.socket()
    s.settimeout(TIMEOUT)
    try:
        s.connect((HOST,PORT))
        s.sendall(cmd_bytes)
        time.sleep(0.05)
        raw = s.recv(8192)
        return raw
    finally:
        try:
            s.close()
        except:
            pass

# Costruisco il comando SETACTIONMAN con il nome esatto ricevuto prima
name = 'CoordinateActionManager(CoordinateActionManagerSDT)'
set_cmd = f'SETACTIONMAN_{name}'.ljust(1000).encode('utf-8')[:1000]
print('Sending SETACTIONMAN...')
raw1 = send_and_recv(set_cmd)
print('RESPONSE1 len', len(raw1))
print('HEX1', raw1.hex())
print('REPR1', repr(raw1.decode('utf-8', errors='replace')))

# Ora invio ACPOS
print('\nSending ACPOS...')
raw2 = send_and_recv('ACPOS'.ljust(10).encode('utf-8'))
print('RESPONSE2 len', len(raw2))
print('HEX2', raw2.hex())
try:
    if len(raw2)>=4:
        length = struct.unpack('<I', raw2[:4])[0]
        payload = raw2[4:4+length]
        print('Payload repr:', repr(payload.decode('utf-8', errors='replace')))
    else:
        print('Decoded:', raw2.decode('utf-8', errors='replace'))
except Exception as e:
    print('Error parsing ACPOS response:', e)
