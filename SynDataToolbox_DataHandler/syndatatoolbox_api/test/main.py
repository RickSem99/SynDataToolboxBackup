"""
main.py
Sistema di Acquisizione Integrato (All-in-One).
Versione 5.0: Input Globale (Funziona anche mentre usi Unreal).
Tasti: 'P' per salvare punto, 'L' per terminare.
"""

import sys
import os
import time
import json
import socket
import ctypes  # ✅ Libreria per leggere tastiera in background su Windows
from config_manager import ConfigManager
from grid_manager import GridManager
from acquisition_engine import AcquisitionEngine


# ==============================================================================
# UTILS PER INPUT GLOBALE (WINDOWS)
# ==============================================================================
def is_key_pressed(v_key):
    """Rileva se un tasto è premuto anche se la finestra non ha il focus"""
    return (ctypes.windll.user32.GetAsyncKeyState(v_key) & 0x8000) != 0


# Codici Tasti Virtuali (Hex)
VK_P = 0x50  # Tasto 'P' per salvare Punto
VK_L = 0x4C  # Tasto 'L' per finire (Leave)
VK_SPACE = 0x20


# ==============================================================================
# FUNZIONE DI REGISTRAZIONE IBRIDA (AUTO o MANUALE)
# ==============================================================================
def record_trajectory_live(host, port, output_file, manual_trigger=False):
    """
    Registra la traiettoria.
    - Se manual_trigger=False: Registra mentre ti muovi + Auto-Stop (5s).
    - Se manual_trigger=True:  Registra SOLO quando premi 'P'. Stop con 'L'.
    """
    print("\n" + "🔴" * 40)
    if manual_trigger:
        print("  MODALITÀ REGISTRAZIONE MANUALE (INPUT GLOBALE)")
        print("  1. Vai su Unreal e muovi l'oggetto.")
        print("  2. Premi [P] sulla tastiera per salvare il punto.")
        print("  3. Premi [L] per terminare la registrazione.")
        print("  (Non serve cliccare sulla finestra Python!)")
    else:
        print("  MODALITÀ REGISTRAZIONE CONTINUA (AUTO-STOP)")
        print("  1. Muovi l'oggetto (registra automaticamente).")
        print("  2. Fermati per 5 secondi per terminare.")
    print("🔴" * 40 + "\n")

    input("👉 Premi INVIO per iniziare...")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(2.0)
        s.connect((host, port))
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return False

    trajectory = []
    start_time = time.time()

    # Variabili per Auto-Mode
    last_pos = None
    last_move_time = time.time()
    STOP_TIMEOUT = 5.0
    MOVEMENT_THRESHOLD = 0.5

    # Debounce per tasti manuali (evita doppi scatti)
    last_key_press_time = 0

    try:
        print(f"🎥 In ascolto... ({'Premi P per salvare' if manual_trigger else 'Muoviti'})")

        while True:
            # 1. Recupero Posizione da Unreal
            current_pos = None
            current_rot = None

            try:
                s.sendall("ACPOS".ljust(10).encode('utf-8'))
                data = s.recv(4096).decode('utf-8', errors='ignore').strip()
                clean_data = data.replace('\x00', '').replace('ERROR', '').strip()

                if "," in clean_data:
                    parts_str = [x.strip() for x in clean_data.split(',') if x.strip()]
                    parts = []
                    for p in parts_str:
                        p_clean = ''.join(c for c in p if c.isdigit() or c == '.' or c == '-')
                        if p_clean: parts.append(float(p_clean))

                    if len(parts) >= 6:
                        current_pos = [parts[0], parts[1], parts[2]]
                        current_rot = [parts[3], parts[4], parts[5]]
            except Exception:
                pass

            if current_pos is None:
                time.sleep(0.05)
                continue

            # ---------------------------------------------------------
            # LOGICA MANUALE (Tasto 'P' Globale)
            # ---------------------------------------------------------
            if manual_trigger:
                # Feedback live
                sys.stdout.write(
                    f"\r👁️ Pos: {int(current_pos[0])},{int(current_pos[1])} | Punti: {len(trajectory)} | Premi [P] Save - [L] End")
                sys.stdout.flush()

                current_time = time.time()

                # Check Tasto 'P' (Save) - Con delay di 0.3s tra pressioni
                if is_key_pressed(VK_P) and (current_time - last_key_press_time > 0.3):
                    point = {
                        "time": round(time.time() - start_time, 3),
                        "loc": current_pos,
                        "rot": current_rot
                    }
                    trajectory.append(point)
                    print(f"\n✅ Punto {len(trajectory)} SALVATO! (Pos: {int(current_pos[0])}, {int(current_pos[1])})")
                    last_key_press_time = current_time

                # Check Tasto 'L' (Leave/End)
                elif is_key_pressed(VK_L) and (current_time - last_key_press_time > 1.0):
                    print("\n🛑 Comando di fine ricevuto.")
                    break

            # ---------------------------------------------------------
            # LOGICA AUTOMATICA (Continua + Auto-Stop)
            # ---------------------------------------------------------
            else:
                is_moving = False
                if last_pos is not None:
                    dist = sum([(a - b) ** 2 for a, b in zip(current_pos, last_pos)]) ** 0.5
                    if dist > MOVEMENT_THRESHOLD:
                        is_moving = True
                        last_move_time = time.time()
                else:
                    is_moving = True
                    last_move_time = time.time()

                if is_moving:
                    point = {
                        "time": round(time.time() - start_time, 3),
                        "loc": current_pos,
                        "rot": current_rot
                    }
                    trajectory.append(point)
                    last_pos = current_pos

                    sys.stdout.write(
                        f"\r⏺ REC: {len(trajectory)} pts | Pos: {int(current_pos[0])},{int(current_pos[1])} | Fermo da: {time.time() - last_move_time:.1f}s")
                    sys.stdout.flush()

                if len(trajectory) > 5 and (time.time() - last_move_time > STOP_TIMEOUT):
                    print(f"\n\n🛑 Rilevato stop movimento ({STOP_TIMEOUT}s). Terminazione...")
                    break

            time.sleep(0.05)  # Loop veloce per input reattivo

    except KeyboardInterrupt:
        print("\n\n⏹ Stop manuale (CTRL+C).")
    finally:
        s.close()

    if len(trajectory) == 0:
        print("\n⚠️ Nessun punto registrato.")
        return False

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(trajectory, f, indent=4)
        print(f"💾 Traiettoria salvata: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("\n" + "=" * 70)
    print("🎬 SISTEMA DI ACQUISIZIONE DATASET (ALL-IN-ONE v5)")
    print("=" * 70 + "\n")

    # 1. SETUP PROGETTO
    default_proj = "UndergroundSubway"
    project_name = input(f"📦 Nome Progetto [{default_proj}]: ").strip() or default_proj

    user_docs = os.path.join(os.path.expanduser("~"), "Documents")
    BASE_UE_PATH = os.path.join(user_docs, "Unreal Projects", project_name, "Saved")

    if not os.path.exists(BASE_UE_PATH):
        print(f"⚠️  Cartella Saved non trovata. Uso cartella corrente.")
        BASE_UE_PATH = os.getcwd()

    UE_PORT = 9734
    UE_ADDRESS = 'localhost'

    # 2. SCELTA FLUSSO
    print("\n" + "=" * 70)
    print("SCELTA MODALITÀ")
    print("=" * 70)
    print("  1. 🎥 REGISTRA NUOVA TRAIETTORIA (Live)")
    print("  2. 📂 Carica traiettoria esistente")
    print("  3. 🧊 Grid Mode (Bounding Box)")

    choice = input("\n👉 Scelta [1]: ").strip() or "1"
    trajectory_file = os.path.join(BASE_UE_PATH, "recorded_path.json")
    ACQUISITION_MODE = "TRAJECTORY"

    # 3. LOGICA DI REGISTRAZIONE
    if choice == "1":
        print("\n  --- TIPO DI REGISTRAZIONE ---")
        print("  A. Continua (Registra tutto mentre ti muovi + Auto-Stop)")
        print("  B. Manuale (Muovi in Unreal, premi 'P' per salvare, 'L' per finire)")
        rec_type = input("\n👉 Scelta [A/B]: ").strip().upper()

        manual_mode = (rec_type == 'B')

        success = record_trajectory_live(UE_ADDRESS, UE_PORT, trajectory_file, manual_trigger=manual_mode)
        if not success:
            print("❌ Registrazione annullata.")
            sys.exit(1)

    elif choice == "2":
        if not os.path.exists(trajectory_file):
            print(f"❌ File non trovato: {trajectory_file}")
            sys.exit(1)
        print(f"✅ File caricato: {trajectory_file}")

    elif choice == "3":
        ACQUISITION_MODE = "GRID"

    # 4. CONFIGURAZIONE PARAMETRI
    print("\n" + "=" * 70)
    print("CONFIGURAZIONE PARAMETRI DI SCATTO")
    print("=" * 70)
    config_manager = ConfigManager()
    is_trajectory = (ACQUISITION_MODE == "TRAJECTORY")
    config = config_manager.get_user_input(trajectory_mode=is_trajectory)

    if is_trajectory:
        config['lookat_poi'] = False

    # 5. OUTPUT
    DEFAULT_OUT = os.path.join(BASE_UE_PATH, "CameraScreenshots")
    user_out = input(f"\n📂 Output [{DEFAULT_OUT}]: ").strip()
    OUTPUT_BASE_DIR = os.path.abspath(user_out) if user_out else DEFAULT_OUT
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    # 6. MOTORE ACQUISIZIONE
    print("\n🔌 Connessione Engine...")
    engine = AcquisitionEngine(config, [], OUTPUT_BASE_DIR, UE_PORT, UE_ADDRESS)

    if not engine.connect():
        sys.exit(1)

    try:
        if ACQUISITION_MODE == "TRAJECTORY":
            success = engine.run_acquisition_trajectory(trajectory_file, delay_between_shots=0.1)
        else:
            bbox_file = os.path.join(BASE_UE_PATH, "VolumeMisure.txt")
            if not os.path.exists(bbox_file):
                print("❌ Manca VolumeMisure.txt")
                sys.exit(1)
            excl_zones = engine.get_exclusion_zones_from_unreal()
            gm = GridManager(bbox_file, config['num_cubes'], excl_zones)
            if gm.calculate_grid():
                engine.grid_positions = gm.get_positions()
                engine._calculate_totals()
                engine.run_acquisition(delay_between_shots=0.1)

        if success:
            print("\n✅ CICLO COMPLETATO CON SUCCESSO!")

    except KeyboardInterrupt:
        print("\n⏹ Interrotto.")
    finally:
        engine.disconnect()


if __name__ == '__main__':
    main()