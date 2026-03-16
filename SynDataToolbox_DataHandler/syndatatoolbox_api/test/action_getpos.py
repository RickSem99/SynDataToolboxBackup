import socket, struct, time
HOST='localhost'
PORT=9734
TIMEOUT=2.0

cmd = 'ACTION_CoordinateActionManager(CoordinateActionManagerSDT)_GETPOS'.ljust(100).encode('utf-8')
print('Sending:', cmd[:80])
try:
    s=socket.socket()
    s.settimeout(TIMEOUT)
    s.connect((HOST,PORT))
    s.sendall(cmd)
    time.sleep(0.05)
    resp = s.recv(1024)
    print('RESP len', len(resp), 'HEX', resp.hex())
    try:
        print('RESP repr', repr(resp.decode('utf-8', errors='replace')))
    except:
        pass
finally:
    try:
        s.close()
    except:
        pass

print('Done. Check Output Log in Unreal for the "📍 Position" log entry from CoordinateActionManagerSDT::GetPosition (it prints X,Y,Z).')
