import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so package imports work when executing the script directly
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from syndatatoolbox_api.isar_socket import IsarSocket

HOST = 'localhost'
PORT = 9734


def safe_decode(b: bytes) -> str:
    try:
        return b.decode('utf-8', errors='replace')
    except Exception:
        return repr(b)


def main():
    print(f"Connecting to {HOST}:{PORT} using IsarSocket protocol...")
    try:
        s = IsarSocket(PORT, HOST)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    try:
        print("\n--- Requesting ACTIONS ---")
        s.send_command('ACTIONS')
        resp = s.rec_bytes(1)[0]
        print("ACTIONS raw:", repr(safe_decode(resp)))

        print("\n--- Requesting ACPOS ---")
        s.send_command('ACPOS')
        resp2 = s.rec_bytes(1)[0]
        print("ACPOS raw:", repr(safe_decode(resp2)))

    except Exception as e:
        print(f"Error during protocol requests: {e}")
    finally:
        try:
            s.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
