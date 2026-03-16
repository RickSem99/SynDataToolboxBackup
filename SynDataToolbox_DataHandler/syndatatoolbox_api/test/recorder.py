"""
recorder.py
Script autonomo per registrare traiettorie (Coordinate + Rotazione) da Unreal Engine.
Compatibile con il sistema APIGateway ACPOS.
Architettura: una connessione TCP per ogni comando (il server chiude dopo ogni risposta).
"""

import socket
import time
import json
import sys
import os
import struct
from typing import Optional

# ==============================================================================
# CONFIGURAZIONE
# ==============================================================================
HOST = 'localhost'
PORT = 9734
FILENAME = "recorded_path.json"
SAMPLING_RATE = 1.0       # secondi tra un campione ACPOS e il successivo
SOCKET_TIMEOUT = 3.0      # timeout per ogni connessione
SIMULATE_FLAG = "--simulate"
# ==============================================================================


def get_output_path():
    print("-" * 60)
    default_proj = "UndergroundSubway"
    project_name = input(f"📦 Inserisci nome progetto Unreal [{default_proj}]: ").strip()
    if not project_name:
        project_name = default_proj
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")
    target_dir = os.path.join(user_documents, "Unreal Projects", project_name, "Saved")
    target_file = os.path.join(target_dir, FILENAME)
    if os.path.exists(target_dir):
        return target_file
    else:
        print(f"⚠️  Cartella non trovata: {target_dir}")
        print(f"   -> Salvataggio nella cartella corrente.")
        return os.path.abspath(FILENAME)


def send_command(cmd: str, pad_to: int = 200) -> bytes:
    """
    Apre una connessione TCP, invia il comando (padded), riceve la risposta, chiude.
    Restituisce i bytes grezzi ricevuti, oppure b'' in caso di errore/timeout.
    """
    raw = b''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(SOCKET_TIMEOUT)
    try:
        s.connect((HOST, PORT))
        padded = cmd.ljust(pad_to).encode('utf-8')
        s.sendall(padded)
        time.sleep(0.05)          # piccola pausa per dare tempo al server di rispondere
        raw = s.recv(8192)
    except socket.timeout:
        pass
    except Exception:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass
    return raw


def decode_payload(raw: bytes) -> str:
    """
    Decodifica la risposta del server:
    - Se ha prefisso 4-byte length (little-endian), usa quello.
    - Altrimenti decodifica raw direttamente.
    """
    if not raw:
        return ''
    if len(raw) >= 4:
        try:
            length = struct.unpack('<I', raw[:4])[0]
            if 0 < length <= len(raw) - 4:
                return raw[4:4 + length].decode('utf-8', errors='ignore').strip()
        except Exception:
            pass
    return raw.decode('utf-8', errors='ignore').strip()


def server_is_up() -> bool:
    """Verifica se il server TCP è raggiungibile (senza inviare comandi)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((HOST, PORT))
        s.close()
        return True
    except Exception:
        return False


def get_coord_manager_name() -> Optional[str]:
    """
    Invia ACTIONS e restituisce il nome del primo CoordinateActionManager trovato.
    """
    raw = send_command("ACTIONS", pad_to=10)
    text = decode_payload(raw).replace('\x00', '').strip()
    if not text:
        return None
    for token in text.split(' '):
        token = token.strip()
        if not token:
            continue
        name = token.split('#')[0]
        if 'CoordinateActionManager' in name:
            return name
    return None


def do_handshake(coord_name: str) -> bool:
    """
    Invia SETACTIONMAN per impostare il CurrentActionManager sul server.
    Restituisce True se il server ha risposto con byte != 0x00.
    """
    raw = send_command(f"SETACTIONMAN_{coord_name}", pad_to=200)
    if not raw:
        print("⚠️  SETACTIONMAN: nessuna risposta dal server.")
        return False
    # Il server risponde con 1 byte: 0x01 = successo, 0x00 = fallito
    ok = raw[0] != 0
    status = "✅ OK" if ok else "❌ FALLITO"
    print(f"🔧 SETACTIONMAN → {status}  (hex: {raw.hex()})")
    return ok


def request_acpos() -> str:
    """
    Invia ACPOS e restituisce il payload testuale (es. '1170.00,-90.00,160.00,0.00,0.00,0.00').
    """
    raw = send_command("ACPOS", pad_to=10)
    return decode_payload(raw).replace('\x00', '').replace('ERROR', '').strip()


def request_getpos(coord_name: str) -> str:
    """
    Invia ACTION_<name>_GETPOS — non richiede SETACTIONMAN.
    Dopo la rebuild restituisce la stringa di posizione direttamente.
    """
    cmd = f"ACTION_{coord_name}_GETPOS"
    raw = send_command(cmd, pad_to=len(cmd) + 10)
    if not raw:
        return ''
    # Se è 1 byte è la vecchia versione (solo esito) — non abbiamo le coordinate
    if len(raw) == 1:
        return ''
    return decode_payload(raw).replace('\x00', '').replace('ERROR', '').strip()


def main():
    print("\n" + "=" * 60)
    print("🎥 REGISTRATORE PERCORSO UNREAL ENGINE (ACPOS MODE)")
    print("=" * 60)

    output_file = get_output_path()
    simulate = SIMULATE_FLAG in sys.argv

    print(f"📂 Output target: {output_file}")
    print("-" * 60)
    print("ISTRUZIONI:")
    print("1. Assicurati che Unreal sia in PLAY")
    print("2. Muovi il CoordinateActionManager nella scena")
    print("3. Premi CTRL+C per TERMINARE e SALVARE")
    print("-" * 60)

    trajectory = []

    try:
        start_time = time.time()

        # ── modalità simulazione ──────────────────────────────────────────────
        if simulate:
            print('\n🧪 SIMULAZIONE avviata (campionamento ogni %.1f s)\n' % SAMPLING_RATE)
            x = 0.0
            while True:
                elapsed = time.time() - start_time
                parts = [x, 0.0, 50.0, 0.0, x * 2, 0.0]
                trajectory.append({"time": round(elapsed, 3),
                                   "loc": parts[:3], "rot": parts[3:]})
                sys.stdout.write(
                    f'\r[{elapsed:06.2f}s] Pos: ({parts[0]:.2f}, {parts[1]:.2f}, {parts[2]:.2f}) '
                    f'| Rot: (P={parts[3]:.2f}, Y={parts[4]:.2f}, R={parts[5]:.2f}) '
                    f'| Punti: {len(trajectory)}'
                )
                sys.stdout.flush()
                x += 10.0
                time.sleep(SAMPLING_RATE)

        # ── modalità reale ────────────────────────────────────────────────────
        else:
            # 1) attendi che il server sia online
            print("⏳ Attendo APIGateway su %s:%d ... (Ctrl+C per uscire)" % (HOST, PORT))
            while not server_is_up():
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(1.0)
            print('\n✅ Server raggiungibile!')

            # 2) ottieni il nome del CoordinateActionManager
            print("🔍 Richiedo lista ActionManagers...")
            coord_name = None
            for attempt in range(5):
                coord_name = get_coord_manager_name()
                if coord_name:
                    break
                time.sleep(0.5)

            if not coord_name:
                print("❌ Nessun CoordinateActionManager trovato. Controlla che Unreal sia in Play.")
                return
            print(f"✅ Trovato: '{coord_name}'")

            # 3) invia SETACTIONMAN (connessione dedicata)
            print("🔧 Impostando CurrentActionManager...")
            ok = do_handshake(coord_name)
            if not ok:
                print("⚠️  SETACTIONMAN non confermato — le coordinate potrebbero essere zero.")
                print("   Verifica che la rebuild includa le modifiche a APIGateway.cpp.")

            print(f'\n🔴 REGISTRAZIONE AVVIATA (ogni {SAMPLING_RATE:.1f}s) — CTRL+C per fermare\n')

            # 4) loop di campionamento: usa ACTION GETPOS (non serve SETACTIONMAN)
            #    con fallback su ACPOS se la rebuild non è ancora disponibile
            zero_warned = False
            old_version_warned = False
            while True:
                # Prima prova con ACTION GETPOS (funziona senza SETACTIONMAN dopo rebuild)
                data = request_getpos(coord_name)

                # Fallback su ACPOS se GETPOS non restituisce coordinate (vecchia versione)
                if not data or ',' not in data:
                    data = request_acpos()
                    if data and ',' in data and not old_version_warned:
                        old_version_warned = True
                        print("\nℹ️  Usando ACPOS (GETPOS non disponibile — rebuild necessaria per GETPOS diretto)")

                if data and ',' in data:
                    try:
                        parts = [float(v) for v in data.split(',') if v.strip()]
                        if len(parts) >= 6:
                            if all(p == 0.0 for p in parts) and not zero_warned:
                                print(f"\n⚠️  Coordinate ancora zero — "
                                      f"prova a muovere il CoordinateActionManager nella scena.")
                                zero_warned = True

                            elapsed = time.time() - start_time
                            trajectory.append({
                                "time": round(elapsed, 3),
                                "loc":  [parts[0], parts[1], parts[2]],
                                "rot":  [parts[3], parts[4], parts[5]]
                            })
                            sys.stdout.write(
                                f'\r[{elapsed:06.2f}s] '
                                f'Pos: ({parts[0]:.2f}, {parts[1]:.2f}, {parts[2]:.2f}) | '
                                f'Rot: (P={parts[3]:.2f}, Y={parts[4]:.2f}, R={parts[5]:.2f}) | '
                                f'Punti: {len(trajectory)}'
                            )
                            sys.stdout.flush()
                    except ValueError:
                        pass

                time.sleep(SAMPLING_RATE)

    except KeyboardInterrupt:
        print("\n\n⏹ Stop manuale ricevuto.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
    finally:
        print("-" * 60)
        if trajectory:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(trajectory, f, indent=4)
                print(f"✅ Salvato: {output_file}  ({len(trajectory)} punti)")
            except Exception as e:
                print(f"❌ Errore salvataggio: {e}")
                with open("backup_path.json", 'w') as f:
                    json.dump(trajectory, f)
                print("⚠️  Backup locale: backup_path.json")
        else:
            print("⚠️  Nessun punto registrato.")
        print("=" * 60)


if __name__ == "__main__":
    main()
