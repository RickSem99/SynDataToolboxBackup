"""
recorder.py
Script autonomo per registrare traiettorie (Coordinate + Rotazione) da Unreal Engine.
Compatibile con il sistema APIGateway ACPOS.
richiede input nome progetto
"""

import socket
import time
import json
import sys
import os

# ==============================================================================
# CONFIGURAZIONE TECNICA
# ==============================================================================
HOST = 'localhost'
PORT = 9734
FILENAME = "recorded_path.json"

# Frequenza di campionamento (secondi)
# 0.1 = 10Hz (molto fluido), 0.2 = 5Hz (più leggero)
SAMPLING_RATE = 0.1


# ==============================================================================

def get_output_path():
    """
    Chiede all'utente il nome del progetto e costruisce il percorso.
    Cerca in: Documents/Unreal Projects/{NomeProgetto}/Saved/
    """
    print("-" * 60)
    default_proj = "UndergroundSubway"
    project_name = input(f"📦 Inserisci nome progetto Unreal [{default_proj}]: ").strip()

    if not project_name:
        project_name = default_proj

    # Ottiene il percorso documenti dell'utente corrente in modo dinamico
    # Funziona su Windows/Linux/Mac
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")

    # Costruisce il percorso standard di Unreal
    target_dir = os.path.join(user_documents, "Unreal Projects", project_name, "Saved")
    target_file = os.path.join(target_dir, FILENAME)

    # Verifica se la cartella esiste
    if os.path.exists(target_dir):
        return target_file
    else:
        print(f"⚠️  Attenzione: Cartella progetto non trovata in: {target_dir}")
        print(f"   -> Il file verrà salvato nella cartella corrente di questo script.")
        return os.path.abspath(FILENAME)


def main():
    print("\n" + "=" * 60)
    print("🎥 REGISTRATORE PERCORSO UNREAL ENGINE (ACPOS MODE)")
    print("=" * 60)

    # 1. Determina percorso di salvataggio
    output_file = get_output_path()

    print(f"📂 Output target: {output_file}")
    print("-" * 60)
    print("ISTRUZIONI:")
    print("1. Assicurati che Unreal sia in PLAY")
    print("2. Assicurati di controllare l'oggetto 'CoordinateActionManager'")
    print("   (Premi F8 per Eject/Possess o seleziona l'actor nel World Outliner)")
    print("3. Muovi l'oggetto lungo il percorso desiderato")
    print("4. Premi CTRL+C in questa finestra per TERMINARE e SALVARE")
    print("-" * 60)

    # Connessione
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(2.0)  # Timeout connessione
        s.connect((HOST, PORT))
        print(f"✅ Connesso a Unreal Engine ({HOST}:{PORT})")
        print("🔴 REGISTRAZIONE AVVIATA... (Premi Ctrl+C per stop)\n")
    except (ConnectionRefusedError, socket.timeout):
        print("❌ Errore: Impossibile connettersi a Unreal Engine.")
        print("   -> Verifica che il gioco sia in PLAY.")
        print("   -> Verifica che APIGateway sia presente nel livello.")
        return

    trajectory = []

    try:
        start_time = time.time()
        while True:
            # 1. Invia comando ACPOS (Action Current Position)
            command = "ACPOS".ljust(10)
            s.sendall(command.encode('utf-8'))

            # 2. Ricevi risposta
            try:
                data = s.recv(4096).decode('utf-8', errors='ignore').strip()
            except socket.timeout:
                continue

            # Pulizia dati
            data = data.replace('\x00', '').replace('ERROR', '')

            if "," in data:
                try:
                    parts = [float(x) for x in data.split(',')]
                    if len(parts) >= 6:
                        point = {
                            "time": round(time.time() - start_time, 3),  # Timestamp relativo
                            "loc": [parts[0], parts[1], parts[2]],
                            "rot": [parts[3], parts[4], parts[5]]  # Pitch, Yaw, Roll
                        }
                        trajectory.append(point)

                        # Feedback visivo
                        sys.stdout.write(
                            f"\r⏺ Punti: {len(trajectory)} | Pos: ({parts[0]:.0f}, {parts[1]:.0f}, {parts[2]:.0f})")
                        sys.stdout.flush()
                except ValueError:
                    pass

            time.sleep(SAMPLING_RATE)

    except KeyboardInterrupt:
        print("\n\n⏹ Stop manuale ricevuto.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
    finally:
        s.close()

    # Salvataggio su file
    print("-" * 60)
    if len(trajectory) > 0:
        try:
            # Crea directory se necessario (nel caso di path locali strani)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(trajectory, f, indent=4)
            print(f"✅ Salvataggio completato con successo!")
            print(f"📄 {output_file}")
            print(f"📊 Totale punti: {len(trajectory)}")
        except Exception as e:
            print(f"❌ Errore durante il salvataggio: {e}")
            # Backup locale
            with open("backup_path.json", 'w') as f:
                json.dump(trajectory, f)
            print("⚠️ Salvato backup locale: backup_path.json")
    else:
        print("⚠️ Nessun punto registrato.")
    print("=" * 60)


if __name__ == "__main__":
    main()