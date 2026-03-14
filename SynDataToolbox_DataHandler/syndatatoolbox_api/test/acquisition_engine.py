"""
acquisition_engine.py
Gestisce il ciclo di acquisizione immagini con controllo camera e spotlight SOLIDALE.
VERSIONE: Luce attaccata alla camera (ActionManager unico).
Include supporto per Grid Mode e Trajectory Replay Mode.
"""

import cv2
import numpy as np
import time
import os
import json
import re  # <-- AGGIUNTO
from datetime import datetime  # <-- AGGIUNTO
from typing import List, Tuple, Dict, Optional
from scipy.spatial.transform import Rotation as R
from syndatatoolbox_api.environment import Environment

# Costante per il Roll (in gradi)
ROLL_DEG = 0.0


class AcquisitionEngine:
    """Motore di acquisizione immagini con gestione camera e spotlight solidale"""

    def __init__(self, config: Dict, grid_positions: List[Tuple[float, float, float]],
                 output_base_dir: str, port: int = 9734, address: str = 'localhost'):
        """
        Inizializza il motore di acquisizione
        """
        self.config = config
        self.grid_positions = grid_positions
        # self.output_base_dir = output_base_dir # <-- LOGICA SPOSTATA
        self.port = port
        self.address = address

        # ==========================================================
        # NUOVA LOGICA: Gestione Sottocartella Esperimento
        # ==========================================================
        print("\n" + "=" * 70)
        print("📂 CONFIGURAZIONE CARTELLA OUTPUT")
        print(f"   Directory Base: {output_base_dir}")

        # 1. Chiedi nome esperimento
        user_exp_name = input("   Nome esperimento (invio per default) > ").strip()

        if not user_exp_name:
            # 2. Crea nome default se input vuoto
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            experiment_name = f"esperimento_{timestamp}"
            print(f"   → Utilizzo nome default: {experiment_name}")
        else:
            # 3. Sanitizza nome custom
            experiment_name = self._sanitize_foldername(user_exp_name)
            if not experiment_name:  # Se il nome era solo caratteri non validi
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                experiment_name = f"esperimento_sanitized_{timestamp}"
            print(f"   → Utilizzo nome: {experiment_name}")

        # 4. Assegna il percorso finale (Base + Sottocartella)
        self.output_base_dir = os.path.join(output_base_dir, experiment_name)

        try:
            os.makedirs(self.output_base_dir, exist_ok=True)
            print(f"✅ Screenshot salvati in: {self.output_base_dir}")
        except OSError as e:
            print(f"❌ ERRORE: Impossibile creare directory: {e}")
            # Fermiamo l'esecuzione se non possiamo scrivere i dati
            raise e
        print("=" * 70 + "\n")
        # ==========================================================

        # VARIABILI DI STATO
        self.current_cam_pos = [0.0, 0.0, 0.0]
        self.lookat_poi_enabled = config.get('lookat_poi', False)
        self.target_poi_pos: Optional[np.ndarray] = None

        # SPOTLIGHT PARAMETERS
        self.spotlight_pitch = config.get('spotlight_pitch', 0.0)
        self.spotlight_yaw = config.get('spotlight_yaw', 0.0)

        self.inner_cone_angles = config.get('inner_cone_angles', [10.0])
        self.outer_cone_angles = config.get('outer_cone_angles', [44.0])

        # Setup environment
        self.setup = {
            'show': None,
            'render': None,
            'max_depth': 200.0,
            'image_folder_path': None,
            'video_path': None
        }

        # Nomi action managers
        # In modalità SOLIDALE usiamo solo il manager della camera per il movimento.
        self.action_manager_cam = "CoordinateActionManager(CoordinateActionManagerSDT)"
        self.light_control_manager = "LightControlActionManager(LightControlActionManagerSDT)"
        self.sensor_list = ["RGBCamera(CameraSDT)"]

        # Contatori
        self.total_shots = 0
        self.current_shot = 0

        # Calcola totale acquisizioni (default grid)
        self._calculate_totals()

        # Environment (inizializzato dopo)
        self.env: Optional[Environment] = None

    # <-- METODO HELPER AGGIUNTO -->
    def _sanitize_foldername(self, name: str) -> str:
        """Rimuove caratteri non validi per nomi di cartelle."""
        name = name.strip()
        # Rimuove caratteri non validi in Windows/Linux/MacOS
        invalid_chars = r'[\\/*?:"<>|]'
        name = re.sub(invalid_chars, "", name)
        # Sostituisce spazi multipli/singoli con underscore
        name = re.sub(r'\s+', '_', name)
        # Limita la lunghezza (opzionale, ma buona pratica)
        return name[:100]

    def _calculate_lookat_pitch_yaw(self, camera_pos: np.ndarray, target_pos: np.ndarray) -> Tuple[float, float]:
        """
        Calcola gli angoli di Pitch e Yaw (in GRADI) per puntare da camera_pos a target_pos.
        """
        direction = target_pos - camera_pos

        # Yaw (rotazione orizzontale)
        yaw_rad = np.arctan2(direction[1], direction[0])
        yaw_deg = np.rad2deg(yaw_rad)

        if yaw_deg > 180:
            yaw_deg -= 360
        elif yaw_deg < -180:
            yaw_deg += 360

        # Pitch (rotazione verticale)
        horizontal_dist = np.linalg.norm(direction[[0, 1]])
        pitch_rad = np.arctan2(direction[2], horizontal_dist)
        pitch_deg = np.rad2deg(pitch_rad)

        return pitch_deg, yaw_deg

    def _euler_to_quaternion(self, pitch_deg: float, yaw_deg: float, roll_deg: float) -> List[float]:
        """
        Converte Pitch, Yaw, Roll (in gradi) in Quaternione (x, y, z, w)
        """
        rot = R.from_euler('ZYX', [yaw_deg, pitch_deg, roll_deg], degrees=True)
        return rot.as_quat().tolist()

    def _move_camera_to_position(self, x: float, y: float, z: float, qx=0.0, qy=0.0, qz=0.0, qw=1.0):
        """Sposta la telecamera (e la luce solidale) alla posizione specificata"""
        self.current_cam_pos = [x, y, z]

        action = [x, y, z, qx, qy, qz, qw]
        self.env.perform_action(
            self.action_manager_cam,
            {"MOVETO": action}
        )
        # Piccolo delay per stabilizzazione fisica in UE
        time.sleep(0.05)

    def _calculate_totals(self):
        """Calcola numero totale di acquisizioni previste (Modalità Griglia)"""
        num_intensities = len(self.config['intensities'])
        num_colors = len(self.config['colors'])
        num_radiuses = len(self.config['radiuses'])
        num_inner_cone = len(self.inner_cone_angles)
        num_outer_cone = len(self.outer_cone_angles)

        num_light_configs = num_intensities * num_colors * num_radiuses * num_inner_cone * num_outer_cone

        num_rotations_per_pos = len(self.config['pitches']) * len(self.config['yaws'])

        if self.lookat_poi_enabled:
            num_rotations_per_pos += 1

        num_camera_positions = len(self.grid_positions)
        # NOTA: num_light_positions rimosso (Luce Solidale 1:1)

        self.total_shots = (num_light_configs *
                            num_camera_positions *
                            num_rotations_per_pos)

        print(f"\n📊 CALCOLO TOTALE ACQUISIZIONI (GRID MODE):")
        print(f"   Configurazioni luce: {num_light_configs}")
        print(f"   Posizioni camera: {num_camera_positions}")
        print(f"   TOTALE ACQUISIZIONI: {self.total_shots}")
        print()

    def _get_coordinates_raw(self, command: str) -> str:
        """Invia un comando di richiesta coordinate/dati e aspetta la risposta"""
        if self.env is None:
            raise ConnectionError("La connessione Environment non è attiva.")
        try:
            sock = getattr(self.env, '_Environment__sock', None)
            if sock is None: raise AttributeError("Impossibile accedere al socket interno.")
            # print(f"   Invio comando raw: {command}") # Debug opzionale
            sock.send_command(command)
            response_bytes = sock.rec_bytes(1)
            if not response_bytes or not response_bytes[0]: return "ZONES_START::ZONES_END"
            response = response_bytes[0].decode("utf-8").strip()
            return response if response else "ZONES_START::ZONES_END"
        except Exception as e:
            raise ConnectionError(f"Errore nella comunicazione socket per '{command}': {e}")

    def _parse_zone_data(self, data_string: str) -> List[Tuple[float, ...]]:
        """Parsa la stringa grezza ricevuta da Unreal."""
        zones = []
        if data_string == "ZONES_START::ZONES_END": return zones
        if not data_string.startswith("ZONES_START:") or not data_string.endswith(":ZONES_END"):
            return zones
        data_string = data_string[len("ZONES_START:"):-len(":ZONES_END")]
        if not data_string.strip(): return zones

        for part in data_string.split(';'):
            part = part.strip()
            if not part: continue
            try:
                coords = [float(c.strip()) for c in part.split(',')]
                if len(coords) == 6: zones.append(tuple(coords))
            except ValueError:
                pass
        return zones

    def get_exclusion_zones_from_unreal(self) -> List[Tuple[float, ...]]:
        print("\n🌍 Richiesta zone di esclusione a Unreal Engine...")
        try:
            raw_response = self._get_coordinates_raw("EXCLUSIONS")
            zones = self._parse_zone_data(raw_response)
            print(f"✅ Ricevute {len(zones)} zone di esclusione da Unreal.")
            return zones
        except Exception as e:
            print(f"❌ Errore durante comunicazione EXCLUSIONS: {e}")
            return []

    def connect(self) -> bool:
        """Connette all'ambiente Unreal"""
        try:
            print(f"🔌 Connessione a Unreal Engine su {self.address}:{self.port}...")
            self.env = Environment(port=self.port, address=self.address, setup=self.setup)
            print("✅ Connesso!")

            required_managers = [
                self.action_manager_cam,
                self.light_control_manager
            ]

            if not hasattr(self.env, 'action_manager_set'):
                print("❌ ERRORE: Action manager set non disponibile.")
                return False

            for manager_name in required_managers:
                if manager_name not in self.env.action_manager_set:
                    print(f"❌ ERRORE: {manager_name} non trovato!")
                    print(f"📋 ActionManager disponibili: {', '.join(self.env.action_manager_set.keys())}")
                    return False

            if self.lookat_poi_enabled:
                print("🎯 Richiesta coordinate Punto di Interesse (PoI)...")
                try:
                    x, y, z = self.env.get_poi_coordinates()
                    self.target_poi_pos = np.array([x, y, z])
                    print(f"✅ Coordinate PoI acquisite: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
                except Exception as e:
                    print(f"❌ ERRORE: Impossibile ottenere coordinate PoI: {e}")
                    self.lookat_poi_enabled = False

            # Impostazione iniziale direzione spotlight (offset rispetto alla camera)
            print(f"\n💡 Impostazione offset direzione SpotLight:")
            try:
                self.env.perform_action(
                    self.light_control_manager,
                    {"SETDIRECTION": [self.spotlight_pitch, self.spotlight_yaw]}
                )
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Errore impostazione spotlight: {e}")

            return True

        except Exception as e:
            print(f"❌ Errore durante connessione: {e}")
            return False

    def disconnect(self):
        if self.env:
            self.env.close_connection()
            print("🔌 Connessione chiusa")

    def run_acquisition(self, delay_between_shots: float = 0.1) -> bool:
        """Esegue l'acquisizione basata su GRIGLIA (Modalità Solidale)"""
        if not self.env:
            print("❌ Ambiente non connesso.")
            return False

        print("\n" + "=" * 70)
        print("🎬 INIZIO ACQUISIZIONE (GRID - LUCE SOLIDALE)")
        print(f"   Salvataggio in: {self.output_base_dir}")  # <-- AGGIUNTO
        print("=" * 70 + "\n")

        self.current_shot = 0
        interrupted = False

        if self.lookat_poi_enabled and self.target_poi_pos is None:
            self.lookat_poi_enabled = False

        try:
            # CICLO 1: Configurazioni Parametriche Luce
            for intensity in self.config['intensities']:
                for color_name, color_rgb in self.config['colors']:
                    for radius in self.config['radiuses']:
                        for inner_cone in self.inner_cone_angles:
                            for outer_cone in self.outer_cone_angles:

                                if not self._set_light_parameters(
                                        intensity, color_rgb, radius, color_name,
                                        inner_cone, outer_cone):
                                    continue

                                # CICLO 2: Posizioni Camera (Griglia)
                                for cam_idx, (cam_x, cam_y, cam_z) in enumerate(self.grid_positions):

                                    # Muove solo la camera (la luce segue)
                                    self._move_camera_to_position(cam_x, cam_y, cam_z)
                                    cam_pos_np = np.array([cam_x, cam_y, cam_z])

                                    rotation_configs = []

                                    # Rotazione LookAt
                                    if self.lookat_poi_enabled and self.target_poi_pos is not None:
                                        pitch_lookat, yaw_lookat = self._calculate_lookat_pitch_yaw(
                                            cam_pos_np, self.target_poi_pos
                                        )
                                        rotation_configs.append(
                                            {'source': 'LOOKAT', 'pitch_deg': pitch_lookat, 'yaw_deg': yaw_lookat}
                                        )

                                    # Rotazioni Preset
                                    for pitch_deg in self.config['pitches']:
                                        for yaw_deg in self.config['yaws']:
                                            rotation_configs.append(
                                                {'source': 'PRESET', 'pitch_deg': pitch_deg, 'yaw_deg': yaw_deg}
                                            )

                                    # CICLO 3: Rotazioni (Nessun ciclo posizioni luce indipendenti)
                                    for rot_config in rotation_configs:
                                        pitch_deg = rot_config['pitch_deg']
                                        yaw_deg = rot_config['yaw_deg']
                                        rot_source = rot_config['source']

                                        result = self._acquire_single_shot(
                                            pitch_deg, yaw_deg, rot_source,
                                            cam_idx,
                                            intensity, color_name, color_rgb, radius,
                                            inner_cone, outer_cone
                                        )

                                        if result == 'quit':
                                            interrupted = True
                                            break
                                        time.sleep(delay_between_shots)

                                    if interrupted: break
                                if interrupted: break
                            if interrupted: break
                        if interrupted: break
                    if interrupted: break
                if interrupted: break

        except KeyboardInterrupt:
            print("\n\n⚠️ Acquisizione interrotta dall'utente (Ctrl+C)")
            interrupted = True
        except Exception as e:
            print(f"\n\n❌ Errore durante acquisizione: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cv2.destroyAllWindows()

        return not interrupted

    def run_acquisition_trajectory(self, trajectory_file: str, delay_between_shots: float = 0.1) -> bool:
        """
        Esegue l'acquisizione basata su TRAIETTORIA REGISTRATA (Modalità Solidale).
        Legge il file JSON generato da recorder.py.
        """
        if not self.env:
            print("❌ Ambiente non connesso.")
            return False

        if not os.path.exists(trajectory_file):
            print(f"❌ File traiettoria non trovato: {trajectory_file}")
            return False

        with open(trajectory_file, 'r') as f:
            trajectory = json.load(f)

        print(f"\n🎬 INIZIO REPLAY TRAIETTORIA ({len(trajectory)} punti)")
        print(f"   Salvataggio in: {self.output_base_dir}")  # <-- AGGIUNTO

        # Disabilita LookAt e Preset per usare esattamente la rotazione registrata
        self.lookat_poi_enabled = False

        # Calcolo totale approssimativo
        num_light_configs = (len(self.config['intensities']) * len(self.config['colors']) * len(self.inner_cone_angles))
        self.total_shots = len(trajectory) * num_light_configs
        self.current_shot = 0
        interrupted = False

        try:
            # CICLO 1: Configurazioni Luce
            for intensity in self.config['intensities']:
                for color_name, color_rgb in self.config['colors']:
                    # Usiamo il primo raggio e cone angle configurato se non iteriamo su tutto per risparmiare tempo
                    radius = self.config['radiuses'][0]
                    inner_cone = self.inner_cone_angles[0]
                    outer_cone = self.outer_cone_angles[0]

                    if not self._set_light_parameters(intensity, color_rgb, radius, color_name, inner_cone, outer_cone):
                        continue

                    # CICLO 2: Punti Traiettoria
                    for pt_idx, point in enumerate(trajectory):
                        loc = point['loc']
                        rot = point['rot']  # Pitch, Yaw, Roll [Gradi]

                        # 1. Muovi Camera (con quaternione calcolato dalla rotazione registrata)
                        # Nota: Unreal usa Roll, ma recorder.py ha salvato Pitch,Yaw,Roll.
                        qx, qy, qz, qw = self._euler_to_quaternion(rot[0], rot[1], rot[2])

                        # Muove la camera sulla traiettoria
                        self._move_camera_to_position(loc[0], loc[1], loc[2], qx, qy, qz, qw)

                        # 2. Scatta (passando le rotazioni per il nome file)
                        result = self._acquire_single_shot(
                            rot[0], rot[1], "REC",
                            pt_idx,  # Usiamo l'indice traiettoria come "Cam ID"
                            intensity, color_name, color_rgb, radius,
                            inner_cone, outer_cone
                        )

                        if result == 'quit':
                            interrupted = True
                            break

                        time.sleep(delay_between_shots)

                    if interrupted: break
                if interrupted: break

        except KeyboardInterrupt:
            print("\n\n⚠️ Acquisizione interrotta dall'utente.")
            return False
        except Exception as e:
            print(f"❌ Errore replay: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    def _set_light_parameters(self, intensity: float, color_rgb: List[float],
                              radius: float, color_name: str,
                              inner_cone: float, outer_cone: float) -> bool:

        if inner_cone > outer_cone:
            return False

        try:
            print(f"\n{'─' * 40}")
            print(f"💡 CONFIG LUCE: {color_name} Int:{intensity:.0f} Rad:{radius:.0f}")
            print(f"   Cones: In {inner_cone}° / Out {outer_cone}°")
            print(f"{'─' * 40}")

            params_base = color_rgb + [intensity, radius]
            self.env.perform_action(self.light_control_manager, {"SETALL": params_base})
            self.env.perform_action(self.light_control_manager, {"SETINNERCONE": [inner_cone]})
            self.env.perform_action(self.light_control_manager, {"SETOUTERCONE": [outer_cone]})

            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"❌ Errore impostazione spotlight: {e}")
            return False

    def _acquire_single_shot(self, pitch_deg: float, yaw_deg: float, rot_source: str,
                             cam_idx: int,
                             intensity: float, color_name: str,
                             color_rgb: List[float], radius: float,
                             inner_cone: float, outer_cone: float) -> str:
        """Acquisisce singola immagine"""
        self.current_shot += 1

        # Se siamo in grid mode, ri-applichiamo la rotazione.
        # In Trajectory mode il movimento è già stato fatto col quaternione corretto.
        # Per sicurezza ri-inviamo il movimento se source != REC, ma per efficienza qui assumiamo
        # che il movimento sia stato fatto dal chiamante (_move_camera_to_position)

        # Scatto effettivo (Chiede solo l'immagine, il movimento è già stato fatto)
        # Usiamo una chiamata dummy "MOVETO" con la posizione corrente solo per triggerare lo scatto nel plugin
        # se il plugin richiede un comando. Ma env_step vuole un'azione.

        # RICHIEDIAMO LO SCATTO SENZA MUOVERE (Workaround: inviamo posizione corrente)
        # O meglio, se siamo in REC mode, il movimento è già stato fatto.
        # Tuttavia env_step esegue l'azione E POI scatta.
        # Quindi dobbiamo passare l'azione corretta qui.

        target_quat = self._euler_to_quaternion(pitch_deg, yaw_deg, ROLL_DEG)
        if rot_source == "REC":
            # In REC mode, pitch_deg/yaw_deg vengono dal file, quindi il quat è corretto
            pass

        action_cam = self.current_cam_pos + target_quat

        hit, observations = self.env.env_step(
            {self.action_manager_cam: {"MOVETO": action_cam}},
            self.sensor_list
        )

        rgb_image_float = observations[0]
        rgb_image_8bit = (rgb_image_float * 255).astype(np.uint8)
        final_bgr_image = cv2.cvtColor(rgb_image_8bit, cv2.COLOR_RGB2BGR)

        cv2.imshow("RGB Camera", final_bgr_image)

        # Light Index è fisso "Fixed" perché solidale
        light_idx = 0

        self._save_image(
            final_bgr_image, cam_idx, light_idx,
            pitch_deg, yaw_deg, intensity, color_name, color_rgb, radius,
            rot_source, inner_cone, outer_cone
        )

        progress_pct = (self.current_shot / self.total_shots) * 100 if self.total_shots > 0 else 0
        print(f"  [{self.current_shot:06d}/{self.total_shots}] ({progress_pct:5.2f}%) "
              f"Cam({cam_idx:03d}) "
              f"P={pitch_deg:+.0f}° Y={yaw_deg:+.0f}° "
              f"({rot_source}) {color_name}")

        key = cv2.waitKey(1)
        if key == ord('q'): return 'quit'
        return 'ok'

    def _save_image(self, image: np.ndarray, cam_idx: int, light_idx: int,
                    pitch_deg: float, yaw_deg: float, intensity: float,
                    color_name: str, color_rgb: List[float], radius: float,
                    rot_source: str, inner_cone: float, outer_cone: float):

        # NOTA: self.output_base_dir è GIA' il percorso finale (es: .../CameraScreenshots/esperimento_X)
        output_dir = self.output_base_dir

        # Questa riga è sicura perché la cartella è già stata creata in __init__
        # ma la lasciamo per robustezza (anche se non ottimale chiamarla a ogni scatto)
        os.makedirs(output_dir, exist_ok=True)

        color_label = f"R{int(color_rgb[0])}G{int(color_rgb[1])}B{int(color_rgb[2])}"

        filename = (
            f"shot{self.current_shot:06d}_"
            f"{color_label}_"
            f"I{int(intensity)}_"
            f"Rad{int(radius)}_"
            f"IC{int(inner_cone):02d}_"
            f"OC{int(outer_cone):02d}_"
            f"C{cam_idx:03d}_"
            f"LFixed_"  # Indicazione esplicita
            f"S{rot_source}_"
            f"P{int(pitch_deg):+03d}_"
            f"Y{int(yaw_deg):+03d}.png"
        )
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, image)