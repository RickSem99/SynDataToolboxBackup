"""
config_manager.py
Gestisce l'input dell'utente e la configurazione dei parametri di acquisizione
VERSIONE SMART: Adatta le domande in base alla modalità (Griglia o Traiettoria).
"""

import sys
from typing import List, Tuple, Dict
import numpy as np


class ColorPresets:
    """Colori predefiniti RGB (0-255)"""
    COLORS = {
        1: ("Bianco", [255, 255, 255]),
        2: ("Rosso", [255, 0, 0]),
        3: ("Blu", [0, 0, 255]),
        4: ("Verde", [0, 255, 0]),
        5: ("Giallo", [255, 255, 0]),
        6: ("Magenta", [255, 0, 255]),
        7: ("Ciano", [0, 255, 255]),
        8: ("Arancione", [255, 165, 0]),
        9: ("Viola", [128, 0, 128]),
        10: ("Rosa", [255, 192, 203])
    }

    @classmethod
    def get_color_list(cls) -> str:
        """Ritorna una stringa formattata con tutti i colori disponibili"""
        result = "\n🎨 Colori disponibili:\n"
        for idx, (name, rgb) in cls.COLORS.items():
            result += f"  {idx}. {name} - RGB{rgb}\n"
        return result


class RotationPresets:
    """Preset di rotazioni per la camera"""
    PRESETS = {
        'a': {'name': 'Frontale', 'pitches': [0.0], 'yaws': [0.0]},
        'b': {'name': 'Frontale + Laterali (±45°)', 'pitches': [0.0], 'yaws': [-45.0, 0.0, 45.0]},
        'c': {'name': 'Alto Frontale (+45°)', 'pitches': [45.0], 'yaws': [0.0]},
        'd': {'name': 'Alto Completo (+45° + Laterali)', 'pitches': [45.0], 'yaws': [-45.0, 0.0, 45.0]},
        'e': {'name': 'Basso Frontale (-45°)', 'pitches': [-45.0], 'yaws': [0.0]},
        'f': {'name': 'Basso Completo (-45° + Laterali)', 'pitches': [-45.0], 'yaws': [-45.0, 0.0, 45.0]}
    }

    @classmethod
    def get_rotation_list(cls) -> str:
        """Ritorna una stringa formattata con tutte le rotazioni disponibili"""
        result = "\n📐 Angoli di rotazione disponibili:\n"
        for key, preset in cls.PRESETS.items():
            result += f"  {key}. {preset['name']}\n"
        return result


class SpotLightDirectionPresets:
    """Preset direzioni per la spotlight"""
    PRESETS = {
        'a': {'name': 'Verso il basso (Pitch -90°)', 'pitch': -90.0, 'yaw': 0.0},
        'b': {'name': 'Orizzontale frontale (Pitch 0°)', 'pitch': 0.0, 'yaw': 0.0},
        'c': {'name': 'Verso l\'alto (Pitch +45°)', 'pitch': 45.0, 'yaw': 0.0},
        'd': {'name': 'Diagonale destra (Yaw +45°)', 'pitch': 0.0, 'yaw': 45.0},
        'e': {'name': 'Diagonale sinistra (Yaw -45°)', 'pitch': 0.0, 'yaw': -45.0},
        'f': {'name': 'Personalizzato (inserisci Pitch e Yaw)', 'pitch': None, 'yaw': None}
    }

    @classmethod
    def get_direction_list(cls) -> str:
        """Ritorna una stringa formattata con tutte le direzioni disponibili"""
        result = "\n💡 Direzioni SpotLight disponibili:\n"
        for key, preset in cls.PRESETS.items():
            result += f"  {key}. {preset['name']}\n"
        return result


class ConfigManager:
    """Gestisce l'acquisizione e validazione dei parametri di configurazione"""

    def __init__(self):
        self.config = {}

    def get_user_input(self, trajectory_mode: bool = False) -> Dict:
        """
        Acquisisce tutti i parametri dall'utente.
        Args:
            trajectory_mode: Se True, salta le domande su griglia e rotazioni camera.
        """
        print("\n" + "=" * 70)
        print("🎬 CONFIGURAZIONE PARAMETRI ACQUISIZIONE")
        if trajectory_mode:
            print("   (Modalità Traiettoria: Richiesti solo parametri Luce)")
        else:
            print("   (Modalità Griglia: Richiesti parametri Griglia, Luce e Camera)")
        print("=" * 70 + "\n")

        # 1. Numero cubetti (SOLO SE NON IN TRAJECTORY MODE)
        if not trajectory_mode:
            self.config['num_cubes'] = self._get_int_input(
                "📦 Numero di cubetti per la griglia",
                min_val=1, max_val=10000, default=125
            )
        else:
            self.config['num_cubes'] = 0  # Valore dummy

        # 2. Intensità luce (SEMPRE)
        print("\n💡 CONFIGURAZIONE INTENSITÀ LUCE")
        intensity_min = self._get_float_input(
            "  Intensità minima", min_val=0.0, max_val=50000.0, default=1000.0
        )
        intensity_max = self._get_float_input(
            "  Intensità massima", min_val=intensity_min, max_val=50000.0, default=15000.0
        )
        intensity_step = self._get_float_input(
            "  Incremento intensità", min_val=1.0, max_val=intensity_max, default=2000.0
        )

        self.config['intensity_range'] = (intensity_min, intensity_max)
        self.config['intensity_step'] = intensity_step
        self.config['intensities'] = self._generate_range(
            intensity_min, intensity_max, intensity_step
        )

        # 3. Colori luce (SEMPRE)
        print(ColorPresets.get_color_list())
        color_indices = self._get_multiple_choice_input(
            "🎨 Seleziona i colori (es: 1,2,3)",
            valid_range=range(1, 11),
            default=[1, 2, 3]
        )
        self.config['colors'] = [ColorPresets.COLORS[i] for i in color_indices]

        # 4. Raggio attenuazione (SEMPRE)
        print("\n📏 CONFIGURAZIONE RAGGIO ATTENUAZIONE")
        radius_min = self._get_float_input(
            "  Raggio minimo (cm)", min_val=10.0, max_val=10000.0, default=300.0
        )
        radius_max = self._get_float_input(
            "  Raggio massimo (cm)", min_val=radius_min, max_val=10000.0, default=1500.0
        )
        radius_step = self._get_float_input(
            "  Incremento raggio", min_val=1.0, max_val=radius_max, default=300.0
        )

        self.config['radius_range'] = (radius_min, radius_max)
        self.config['radius_step'] = radius_step
        self.config['radiuses'] = self._generate_range(
            radius_min, radius_max, radius_step
        )

        # 4.5. 📐 CONFIGURAZIONE ANGOLI SPOTLIGHT (SEMPRE)
        print("\n" + "=" * 70)
        print("📐 CONFIGURAZIONE ANGOLI SPOTLIGHT (INNER E OUTER CONE)")
        print("=" * 70)

        self.config['inner_cone_angles'] = self._get_cone_angle_input(
            "Inner Cone Angle", min_val=0.0, max_val=90.0, default_val=10.0
        )

        self.config['outer_cone_angles'] = self._get_cone_angle_input(
            "Outer Cone Angle", min_val=0.0, max_val=90.0, default_val=44.0
        )

        # 5. DIREZIONE SPOTLIGHT (SEMPRE - Serve come offset rispetto alla camera)
        print("\n" + "=" * 70)
        print("💡 CONFIGURAZIONE DIREZIONE SPOTLIGHT")
        print("   (Nota: La luce segue la camera. Questi valori inclinano la luce rispetto alla vista)")
        print("=" * 70)
        print(SpotLightDirectionPresets.get_direction_list())

        direction_choice = self._get_choice_input(
            "Seleziona direzione spotlight",
            valid_choices=['a', 'b', 'c', 'd', 'e', 'f'],
            default='a'
        )

        if direction_choice == 'f':
            print("\n📐 Inserisci angoli personalizzati:")
            spotlight_pitch = self._get_float_input(
                "  Pitch (gradi)", min_val=-90.0, max_val=90.0, default=0.0
            )
            spotlight_yaw = self._get_float_input(
                "  Yaw (gradi)", min_val=-180.0, max_val=180.0, default=0.0
            )
        else:
            preset = SpotLightDirectionPresets.PRESETS[direction_choice]
            spotlight_pitch = preset['pitch']
            spotlight_yaw = preset['yaw']
            print(f"✅ Direzione selezionata: {preset['name']}")

        self.config['spotlight_pitch'] = spotlight_pitch
        self.config['spotlight_yaw'] = spotlight_yaw

        # 6. Rotazioni camera VS LookAt PoI (SOLO SE NON IN TRAJECTORY MODE)
        if not trajectory_mode:
            print("\n" + "=" * 70)
            print("🎯 MODALITÀ ORIENTAMENTO TELECAMERA")
            print("=" * 70)
            print("\n⚠️  ATTENZIONE: Puoi scegliere SOLO UNA delle seguenti modalità:\n")
            print("  A) Rotazioni Preset (Pitch/Yaw fissi da lista)")
            print("  B) LookAt PoI (telecamera punta sempre il Punto di Interesse)\n")

            rotation_mode = self._get_rotation_mode_input()

            if rotation_mode == 'preset':
                print(RotationPresets.get_rotation_list())
                rotation_keys = self._get_multiple_choice_input(
                    "📐 Seleziona preset rotazioni (es: a,b,c)",
                    valid_choices=list(RotationPresets.PRESETS.keys()),
                    default=['b']
                )

                pitches_set = set()
                yaws_set = set()
                for key in rotation_keys:
                    preset = RotationPresets.PRESETS[key]
                    pitches_set.update(preset['pitches'])
                    yaws_set.update(preset['yaws'])

                self.config['pitches'] = sorted(list(pitches_set))
                self.config['yaws'] = sorted(list(yaws_set))
                self.config['pitches_rad'] = np.radians(self.config['pitches'])
                self.config['yaws_rad'] = np.radians(self.config['yaws'])
                self.config['lookat_poi'] = False

            else:  # rotation_mode == 'lookat'
                print("\n✅ Modalità LookAt PoI attivata")
                self.config['pitches'] = []
                self.config['yaws'] = []
                self.config['pitches_rad'] = []
                self.config['yaws_rad'] = []
                self.config['lookat_poi'] = True
        else:
            # Configurazione dummy per Trajectory Mode (non usata ma evita errori)
            self.config['pitches'] = [0.0]
            self.config['yaws'] = [0.0]
            self.config['lookat_poi'] = False

        # Riepilogo
        self._print_summary(trajectory_mode)

        confirm = input("\n✅ Confermare configurazione? (s/n) [s]: ").strip().lower()
        if confirm not in ['', 's', 'y', 'yes', 'si']:
            print("❌ Configurazione annullata.")
            sys.exit(0)

        return self.config

    def _get_cone_angle_input(self, prompt_prefix: str, min_val: float, max_val: float, default_val: float) -> List[
        float]:
        """Gestisce l'input per range o valore fisso per i Cone Angle (gradi)."""
        print(f"\n  > {prompt_prefix.upper()}")

        while True:
            mode = input(f"  Vuoi un intervallo per {prompt_prefix} (I) o un valore fisso (F)? [I/F]: ").strip().upper()

            if mode == 'F':
                value = self._get_float_input(
                    f"    Valore fisso (gradi)", min_val=min_val, max_val=max_val, default=default_val
                )
                return [value]

            elif mode == 'I':
                print(f"    Definizione intervallo per {prompt_prefix}:")
                try:
                    start = self._get_float_input(
                        "    Valore minimo (gradi)", min_val=min_val, max_val=max_val, default=min_val
                    )
                    end = self._get_float_input(
                        "    Valore massimo (gradi)", min_val=start, max_val=max_val, default=max_val
                    )
                    step = self._get_float_input(
                        "    Incremento (gradi)", min_val=0.1, max_val=max_val, default=10.0
                    )
                    values = self._generate_range(start, end, step)
                    if not values:
                        print(f"    ⚠️ L'intervallo specificato non genera valori validi. Riprova.")
                        continue
                    print(f"    ✅ Generati {len(values)} valori: {values}")
                    return values
                except Exception:
                    print(f"    ❌ Errore nella definizione dell'intervallo. Riprova.")
            else:
                print(f"    ❌ Scelta non valida. Inserire 'I' o 'F'.")

    def _get_rotation_mode_input(self) -> str:
        """Input per la selezione della modalità di rotazione"""
        while True:
            user_input = input("Seleziona modalità (A o B) [A]: ").strip().lower()

            if user_input == '' or user_input == 'a':
                return 'preset'
            elif user_input == 'b':
                return 'lookat'
            else:
                print(f"  ❌ Scelta non valida. Inserire 'A' o 'B'")

    def _get_choice_input(self, prompt: str, valid_choices: List[str], default: str = None) -> str:
        """Input singola scelta con validazione"""
        while True:
            default_str = f" [{default}]" if default is not None else ""
            user_input = input(f"{prompt}{default_str}: ").strip().lower()

            if user_input == '' and default is not None:
                return default

            if user_input in valid_choices:
                return user_input
            else:
                print(f"  ❌ Scelta non valida. Opzioni: {', '.join(valid_choices)}")

    def _get_int_input(self, prompt: str, min_val: int = None,
                       max_val: int = None, default: int = None) -> int:
        """Input intero con validazione"""
        while True:
            try:
                default_str = f" [{default}]" if default is not None else ""
                user_input = input(f"{prompt}{default_str}: ").strip()
                if user_input == '' and default is not None: return default
                value = int(user_input)
                if min_val is not None and value < min_val:
                    print(f"  ⚠️  Valore minimo: {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"  ⚠️  Valore massimo: {max_val}")
                    continue
                return value
            except ValueError:
                print("  ❌ Inserire un numero intero valido")

    def _get_float_input(self, prompt: str, min_val: float = None,
                         max_val: float = None, default: float = None) -> float:
        """Input float con validazione"""
        while True:
            try:
                default_str = f" [{default}]" if default is not None else ""
                user_input = input(f"{prompt}{default_str}: ").strip()
                if user_input == '' and default is not None: return default
                value = float(user_input)
                if min_val is not None and value < min_val:
                    print(f"  ⚠️  Valore minimo: {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"  ⚠️  Valore massimo: {max_val}")
                    continue
                return value
            except ValueError:
                print("  ❌ Inserire un numero valido")

    def _get_multiple_choice_input(self, prompt: str, valid_range=None,
                                   valid_choices=None, default=None) -> List:
        """Input multiplo con validazione"""
        while True:
            try:
                default_str = f" [{','.join(map(str, default))}]" if default else ""
                user_input = input(f"{prompt}{default_str}: ").strip()
                if user_input == '' and default is not None: return default
                if valid_range:
                    choices = [int(x.strip()) for x in user_input.split(',')]
                    if all(c in valid_range for c in choices):
                        return sorted(list(set(choices)))
                    else:
                        print(f"  ❌ Valori validi: {list(valid_range)}")
                elif valid_choices:
                    choices = [x.strip().lower() for x in user_input.split(',')]
                    if all(c in valid_choices for c in choices):
                        return choices
                    else:
                        print(f"  ❌ Scelte valide: {valid_choices}")
            except ValueError:
                print("  ❌ Formato non valido. Usa virgole per separare (es: 1,2,3)")

    def _generate_range(self, min_val: float, max_val: float, step: float) -> List[float]:
        """Genera lista di valori con range e step"""
        values = []
        current = min_val
        while current <= max_val:
            values.append(round(current, 2))
            current += step
        return values

    def _print_summary(self, trajectory_mode: bool):
        """Stampa riepilogo configurazione adattivo"""
        print("\n" + "=" * 70)
        print("📋 RIEPILOGO CONFIGURAZIONE")
        print("=" * 70)

        if not trajectory_mode:
            print(f"\n📦 Cubetti griglia: {self.config['num_cubes']}")
        else:
            print(f"\n🎥 Modalità Traiettoria: Punti e Rotazioni da file registrato.")

        print(f"\n💡 Intensità luce:")
        print(f"   Range: {self.config['intensity_range'][0]} - {self.config['intensity_range'][1]}")
        print(f"   Valori: {self.config['intensities']}")

        print(f"\n🎨 Colori selezionati ({len(self.config['colors'])}):")
        for name, rgb in self.config['colors']:
            print(f"   - {name}: RGB{rgb}")

        print(f"\n📏 Raggio attenuazione:")
        print(f"   Valori: {self.config['radiuses']}")

        print(f"\n📐 Angoli SpotLight (Cone Angle):")
        print(f"   Inner: {self.config['inner_cone_angles']}")
        print(f"   Outer: {self.config['outer_cone_angles']}")

        print(f"\n💡 Direzione SpotLight (Offset):")
        print(f"   Pitch: {self.config['spotlight_pitch']}°")
        print(f"   Yaw: {self.config['spotlight_yaw']}°")

        if not trajectory_mode:
            print(f"\n📐 Rotazioni camera (Preset):")
            print(f"   Pitch: {self.config['pitches']}")
            print(f"   Yaw: {self.config['yaws']}")
            lookat_enabled = self.config.get('lookat_poi', False)
            print(f"\n🎯 Rotazione LookAt PoI: {'✅ Abilitato' if lookat_enabled else '❌ Disabilitato'}")

        # AGGIORNAMENTO TOTALI
        total_light_configs = (len(self.config['intensities']) *
                               len(self.config['colors']) *
                               len(self.config['radiuses']) *
                               len(self.config['inner_cone_angles']) *
                               len(self.config['outer_cone_angles']))

        print(f"\n📊 TOTALI:")
        print(f"   Configurazioni luce per punto: {total_light_configs}")
        if not trajectory_mode:
            total_rotations = len(self.config['pitches']) * len(self.config['yaws']) + (1 if self.config.get('lookat_poi') else 0)
            print(f"   Rotazioni per posizione: {total_rotations}")
            print(f"   Posizioni griglia: {self.config['num_cubes']}")
        else:
            print(f"   Punti traiettoria: (Definiti nel file)")

        print("=" * 70)