"""
grid_manager.py
Gestisce la creazione e il calcolo della griglia 3D con zone di esclusione ottimizzate
"""

import math
import sys
from typing import List, Tuple, Dict


class GridManager:
    """Gestisce la griglia 3D basata su bounding box con zone di esclusione"""

    def __init__(self, bbox_file_path: str, num_cubes: int,
                 exclusion_zones: List[Tuple[float, ...]] = None):
        """
        Inizializza il gestore griglia

        Args:
            bbox_file_path: Path del file con coordinate bounding box
            num_cubes: Numero di cubetti desiderati
            exclusion_zones: Lista di tuple (CX, CY, CZ, SX, SY, SZ) per le zone di esclusione
        """
        self.bbox_file_path = bbox_file_path
        self.num_cubes = num_cubes

        # Coordinate bounding box
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.min_z = 0.0
        self.max_z = 0.0

        # Dimensioni
        self.width = 0.0
        self.depth = 0.0
        self.height = 0.0
        self.volume = 0.0

        # Griglia
        self.grid_x = 0
        self.grid_y = 0
        self.grid_z = 0
        self.cube_size_x = 0.0
        self.cube_size_y = 0.0
        self.cube_size_z = 0.0

        # Centri dei cubetti
        self.centers: List[Tuple[float, float, float]] = []

        # Zone di esclusione (validate)
        self.exclusion_zones = self._validate_exclusion_zones(exclusion_zones)

    def _validate_exclusion_zones(self, zones: List[Tuple[float, ...]]) -> List[Tuple[float, ...]]:
        """
        Valida e filtra le zone di esclusione

        Args:
            zones: Lista di zone da validare

        Returns:
            Lista di zone valide
        """
        if zones is None:
            return []

        valid_zones = []
        for i, zone in enumerate(zones):
            if len(zone) != 6:
                print(f"⚠️  ATTENZIONE: Zona {i} ignorata - formato invalido (attesi 6 valori, ricevuti {len(zone)})")
                continue

            cx, cy, cz, sx, sy, sz = zone

            # Verifica dimensioni positive
            if sx <= 0 or sy <= 0 or sz <= 0:
                print(f"⚠️  ATTENZIONE: Zona {i} ignorata - dimensioni non positive (SX={sx}, SY={sy}, SZ={sz})")
                continue

            # Verifica valori numerici validi
            if any(not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) for v in zone):
                print(f"⚠️  ATTENZIONE: Zona {i} ignorata - valori numerici non validi")
                continue

            valid_zones.append(zone)

        return valid_zones

    def load_bounding_box(self) -> bool:
        """
        Carica coordinate bounding box da file

        Returns:
            True se caricamento riuscito, False altrimenti
        """
        coords = {}
        try:
            with open(self.bbox_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(('#', '//')):
                        try:
                            key, value = line.split(':')
                            coords[key.strip()] = float(value.strip())
                        except ValueError:
                            continue

            # Estrazione coordinate
            required_keys = ['MinX', 'MaxX', 'MinY', 'MaxY', 'MinZ', 'MaxZ']
            for key in required_keys:
                if key not in coords:
                    raise KeyError(key)

            self.min_x = coords['MinX']
            self.max_x = coords['MaxX']
            self.min_y = coords['MinY']
            self.max_y = coords['MaxY']
            self.min_z = coords['MinZ']
            self.max_z = coords['MaxZ']

            print(f"✅ Bounding Box caricato da: {self.bbox_file_path}")
            print(f"   X: [{self.min_x:.2f}, {self.max_x:.2f}]")
            print(f"   Y: [{self.min_y:.2f}, {self.max_y:.2f}]")
            print(f"   Z: [{self.min_z:.2f}, {self.max_z:.2f}]")

            return True

        except FileNotFoundError:
            print(f"❌ ERRORE: File non trovato: {self.bbox_file_path}")
            return False
        except KeyError as e:
            print(f"❌ ERRORE: Chiave mancante '{e}'. Richieste: {', '.join(required_keys)}")
            return False
        except Exception as e:
            print(f"❌ ERRORE durante lettura file: {str(e)}")
            return False

    def is_inside_exclusion_zone(self, pos: Tuple[float, float, float]) -> bool:
        """
        Verifica se una posizione è all'interno di una zona di esclusione usando AABB

        Args:
            pos: Tupla (x, y, z) da verificare

        Returns:
            True se la posizione è dentro una zona di esclusione, False altrimenti
        """
        px, py, pz = pos

        for cx, cy, cz, sx, sy, sz in self.exclusion_zones:
            # AABB (Axis-Aligned Bounding Box) - Test di intersezione
            # Un punto è dentro se la distanza dal centro è <= metà dimensione per ogni asse
            half_sx = sx / 2.0
            half_sy = sy / 2.0
            half_sz = sz / 2.0

            if (abs(px - cx) <= half_sx and
                    abs(py - cy) <= half_sy and
                    abs(pz - cz) <= half_sz):
                return True

        return False

    def get_zone_statistics(self) -> Dict:
        """
        Calcola statistiche sulle zone di esclusione

        Returns:
            Dizionario con statistiche delle zone
        """
        if not self.exclusion_zones:
            return {
                'count': 0,
                'total_volume': 0.0,
                'zones': []
            }

        zone_stats = []
        total_volume = 0.0

        for i, (cx, cy, cz, sx, sy, sz) in enumerate(self.exclusion_zones):
            volume = sx * sy * sz
            total_volume += volume

            zone_stats.append({
                'index': i,
                'center': (cx, cy, cz),
                'size': (sx, sy, sz),
                'volume': volume
            })

        return {
            'count': len(self.exclusion_zones),
            'total_volume': total_volume,
            'zones': zone_stats
        }

    def calculate_grid(self) -> bool:
        """
        Calcola dimensioni griglia e genera centri cubetti filtrati

        Returns:
            True se calcolo riuscito, False altrimenti
        """
        if not self.load_bounding_box():
            return False

        # Calcola dimensioni
        self.width = self.max_x - self.min_x
        self.depth = self.max_y - self.min_y
        self.height = self.max_z - self.min_z

        if self.width <= 0 or self.depth <= 0 or self.height <= 0:
            print(f"❌ ERRORE: Dimensioni non valide")
            print(f"   Width: {self.width:.2f}, Depth: {self.depth:.2f}, Height: {self.height:.2f}")
            return False

        self.volume = self.width * self.depth * self.height
        cube_volume = self.volume / self.num_cubes
        cube_size = cube_volume ** (1 / 3)

        # Calcola divisioni griglia
        self.grid_x = math.ceil(self.width / cube_size)
        self.grid_y = math.ceil(self.depth / cube_size)
        self.grid_z = math.ceil(self.height / cube_size)

        # Ricalcola dimensioni effettive cubetti
        self.cube_size_x = self.width / self.grid_x
        self.cube_size_y = self.depth / self.grid_y
        self.cube_size_z = self.height / self.grid_z

        # Genera centri INIZIALI
        print(f"\n🔄 Generazione griglia {self.grid_x}x{self.grid_y}x{self.grid_z}...")
        initial_centers = []

        for z in range(self.grid_z):
            for y in range(self.grid_y):
                for x in range(self.grid_x):
                    cx = self.min_x + (x + 0.5) * self.cube_size_x
                    cy = self.min_y + (y + 0.5) * self.cube_size_y
                    cz = self.min_z + (z + 0.5) * self.cube_size_z
                    initial_centers.append((cx, cy, cz))

        initial_count = len(initial_centers)

        # FILTRAGGIO ZONE DI ESCLUSIONE
        if self.exclusion_zones:
            print(f"🔍 Applicazione filtro zone di esclusione ({len(self.exclusion_zones)} zone)...")

            # Mostra statistiche zone
            zone_stats = self.get_zone_statistics()
            print(f"   Volume totale zone: {zone_stats['total_volume']:.2f} cm³")
            print(f"   % volume occupato: {(zone_stats['total_volume'] / self.volume) * 100:.2f}%")

            # Filtraggio con progress
            valid_centers = []
            filtered_count = 0

            for i, center in enumerate(initial_centers):
                if not self.is_inside_exclusion_zone(center):
                    valid_centers.append(center)
                else:
                    filtered_count += 1

                # Progress ogni 10%
                if (i + 1) % max(1, initial_count // 10) == 0:
                    progress = ((i + 1) / initial_count) * 100
                    print(f"   Progresso: {progress:.0f}% ({i + 1}/{initial_count})")

            self.centers = valid_centers

            print(f"\n✅ Filtro completato:")
            print(f"   Posizioni iniziali: {initial_count}")
            print(f"   Posizioni rimosse: {filtered_count}")
            print(f"   Posizioni finali: {len(self.centers)}")
            print(f"   % rimossa: {(filtered_count / initial_count) * 100:.2f}%")
        else:
            self.centers = initial_centers
            print("ℹ️  Nessuna zona di esclusione definita")

        # Riepilogo finale
        print(f"\n📊 GRIGLIA FINALE:")
        print(f"   Dimensioni volume: {self.width:.2f} x {self.depth:.2f} x {self.height:.2f} cm")
        print(f"   Volume totale: {self.volume:.2f} cm³")
        print(f"   Griglia: {self.grid_x} x {self.grid_y} x {self.grid_z}")
        print(f"   Cubetti teorici: {initial_count}")
        print(f"   Cubetti utilizzabili: {len(self.centers)}")
        print(f"   Dimensione cubetto: {self.cube_size_x:.2f} x {self.cube_size_y:.2f} x {self.cube_size_z:.2f} cm")

        if len(self.centers) == 0:
            print("\n❌ ERRORE: Nessuna posizione valida dopo il filtraggio!")
            print("   Verificare che le zone di esclusione non coprano l'intera griglia")
            return False

        return True

    def get_positions(self) -> List[Tuple[float, float, float]]:
        """Ritorna lista di posizioni (centri cubetti) filtrate"""
        return self.centers

    def save_grid_info(self, output_file: str, building_name: str = "BoundingBoxObject") -> bool:
        """
        Salva informazioni griglia su file con dettagli zone di esclusione

        Args:
            output_file: Path file di output
            building_name: Nome oggetto/edificio

        Returns:
            True se salvataggio riuscito, False altrimenti
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write(f"INFORMAZIONI GRIGLIA 3D - {building_name}\n")
                f.write("=" * 70 + "\n\n")

                # Bounding Box
                f.write("BOUNDING BOX:\n")
                f.write(f"  X: [{self.min_x:.2f}, {self.max_x:.2f}] - Ampiezza: {self.width:.2f} cm\n")
                f.write(f"  Y: [{self.min_y:.2f}, {self.max_y:.2f}] - Profondità: {self.depth:.2f} cm\n")
                f.write(f"  Z: [{self.min_z:.2f}, {self.max_z:.2f}] - Altezza: {self.height:.2f} cm\n")
                f.write(f"  Volume totale: {self.volume:.2f} cm³\n\n")

                # Griglia
                f.write("GRIGLIA:\n")
                f.write(f"  Divisioni: {self.grid_x} x {self.grid_y} x {self.grid_z}\n")
                f.write(f"  Cubetti teorici: {self.grid_x * self.grid_y * self.grid_z}\n")
                f.write(
                    f"  Dimensione cubetto: {self.cube_size_x:.2f} x {self.cube_size_y:.2f} x {self.cube_size_z:.2f} cm\n\n")

                # Zone di esclusione
                zone_stats = self.get_zone_statistics()
                f.write("ZONE DI ESCLUSIONE:\n")
                f.write(f"  Numero zone: {zone_stats['count']}\n")

                if zone_stats['count'] > 0:
                    f.write(f"  Volume totale zone: {zone_stats['total_volume']:.2f} cm³\n")
                    f.write(f"  % volume occupato: {(zone_stats['total_volume'] / self.volume) * 100:.2f}%\n\n")

                    for zone_info in zone_stats['zones']:
                        f.write(f"  Zona {zone_info['index']}:\n")
                        f.write(
                            f"    Centro: ({zone_info['center'][0]:.2f}, {zone_info['center'][1]:.2f}, {zone_info['center'][2]:.2f})\n")
                        f.write(
                            f"    Dimensioni: ({zone_info['size'][0]:.2f}, {zone_info['size'][1]:.2f}, {zone_info['size'][2]:.2f})\n")
                        f.write(f"    Volume: {zone_info['volume']:.2f} cm³\n\n")
                else:
                    f.write("  Nessuna zona definita\n\n")

                # Posizioni finali
                initial_count = self.grid_x * self.grid_y * self.grid_z
                filtered_count = initial_count - len(self.centers)

                f.write("POSIZIONI FILTRATE:\n")
                f.write(f"  Posizioni iniziali: {initial_count}\n")
                f.write(f"  Posizioni rimosse: {filtered_count}\n")
                f.write(f"  Posizioni finali: {len(self.centers)}\n")

                if filtered_count > 0:
                    f.write(f"  % rimossa: {(filtered_count / initial_count) * 100:.2f}%\n\n")
                else:
                    f.write("\n")

                f.write("=" * 70 + "\n")
                f.write("ELENCO POSIZIONI (X, Y, Z):\n")
                f.write("=" * 70 + "\n\n")

                for idx, (cx, cy, cz) in enumerate(self.centers):
                    f.write(f"{idx:5d}: {cx:10.2f}, {cy:10.2f}, {cz:10.2f}\n")

            print(f"💾 Informazioni griglia salvate in: {output_file}")
            return True

        except Exception as e:
            print(f"⚠️  Errore salvataggio griglia: {str(e)}")
            return False

    def get_summary(self) -> dict:
        """Ritorna dizionario con riepilogo griglia completo"""
        zone_stats = self.get_zone_statistics()

        return {
            'bbox': {
                'min': (self.min_x, self.min_y, self.min_z),
                'max': (self.max_x, self.max_y, self.max_z)
            },
            'dimensions': {
                'width': self.width,
                'depth': self.depth,
                'height': self.height,
                'volume': self.volume
            },
            'grid': {
                'x': self.grid_x,
                'y': self.grid_y,
                'z': self.grid_z,
                'total_theoretical': self.grid_x * self.grid_y * self.grid_z,
                'total_usable': len(self.centers),
                'filtered_count': (self.grid_x * self.grid_y * self.grid_z) - len(self.centers)
            },
            'cube_size': {
                'x': self.cube_size_x,
                'y': self.cube_size_y,
                'z': self.cube_size_z
            },
            'exclusion_zones': zone_stats,
            'positions': self.centers
        }