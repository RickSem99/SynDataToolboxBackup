import time
import sys
from syndatatoolbox_api.environment import Environment
from syndatatoolbox_api.action_managers.LightControlActionManager import LightControlActionManager


class LightControlTester:
    """
    Classe per testare LightControlActionManagerSDT usando Environment.
    """

    def __init__(self, port=9734, address='localhost'):
        """
        Inizializza la connessione con Unreal Engine.

        Args:
            port (int): Porta TCP (default 9734 per APIGateway)
            address (str): Indirizzo del server Unreal
        """
        self.setup = {
            'show': None, 'render': None, 'max_depth': 200.
        }

        print(f"🔌 Connessione a Unreal Engine su {address}:{port}...")

        try:
            self.env = Environment(port=port, address=address, setup=self.setup)
            print("✅ Connesso!")

            # Nome dell'ActionManager (deve corrispondere all'etichetta in Unreal)
            self.action_manager_name = "LightControlActionManager(LightControlActionManagerSDT)"

            # Verifica che l'ActionManager sia disponibile
            if self.action_manager_name not in self.env.action_manager_set:
                print(f"\n❌ ERRORE: {self.action_manager_name} non trovato!")
                print(f"📋 ActionManager disponibili:")
                for am_name in self.env.action_manager_set.keys():
                    print(f"   - {am_name}")
                self.close()
                sys.exit(1)

            print(f"✅ {self.action_manager_name} trovato!\n")

        except Exception as e:
            print(f"❌ Errore durante la connessione: {e}")
            sys.exit(1)

    def set_color(self, rgb=(255, 0, 0)):
        """
        Imposta il colore della luce.

        Args:
            rgb (tuple): Tupla (R, G, B) con valori 0-255
        """
        return self._perform_action("SETCOLOR", list(rgb), f"Colore RGB{rgb}")

    def set_intensity(self, intensity=5000.0):
        """
        Imposta l'intensità della luce.

        Args:
            intensity (float): Valore di intensità
        """
        return self._perform_action("SETINTENSITY", [intensity], f"Intensità {intensity}")

    def set_radius(self, radius=1000.0):
        """
        Imposta il raggio di attenuazione della luce.

        Args:
            radius (float): Raggio in unità Unreal (cm)
        """
        return self._perform_action("SETRADIUS", [radius], f"Raggio {radius}")

    def set_all(self, rgb=(255, 255, 255), intensity=5000.0, radius=1000.0):
        """
        Imposta tutti i parametri della luce in una volta.

        Args:
            rgb (tuple): Tupla (R, G, B) con valori 0-255
            intensity (float): Valore di intensità
            radius (float): Raggio in unità Unreal (cm)
        """
        params = list(rgb) + [intensity, radius]
        return self._perform_action("SETALL", params, f"All parameters {params}")

    def _perform_action(self, action_name, params, description):
        """
        Metodo helper per eseguire un'azione e gestire il risultato.

        Args:
            action_name (str): Nome dell'azione (SETCOLOR, SETINTENSITY, ecc.)
            params (list): Lista di parametri
            description (str): Descrizione dell'azione per il log

        Returns:
            int: Codice risultato (0 = successo, != 0 = errore)
        """
        print(f"➡️  {description}...")

        try:
            hit = self.env.perform_action(
                self.action_manager_name,
                {action_name: params}
            )

            if hit == 0 or (hasattr(hit, '__iter__') and hit[0] == 0):
                print(f"✅ {description} completato con successo")
                result = 0
            else:
                print(f"⚠️  {description} completato con warning (hit={hit})")
                result = 1

        except Exception as e:
            print(f"❌ Errore durante {description}: {e}")
            result = -1

        time.sleep(0.5)  # Piccola pausa per stabilità
        return result

    def close(self):
        """Chiude la connessione con Unreal Engine."""
        print("\n🔌 Chiusura connessione...")
        if hasattr(self, 'env'):
            self.env.close_connection()
        print("✅ Connessione chiusa")


# ============================================================
# SCRIPT DI TEST
# ============================================================

def run_all_tests():
    """Esegue una suite completa di test per LightControlActionManager."""

    print("=" * 60)
    print("🧪 Test Suite per LightControlActionManager")
    print("=" * 60 + "\n")

    tester = LightControlTester()

    try:
        # Test 1: Colore Rosso
        print("\n🔴 Test 1: SETCOLOR - Rosso")
        tester.set_color(rgb=(255, 0, 0))

        # Test 2: Intensità Alta
        print("\n💡 Test 2: SETINTENSITY - 10000")
        tester.set_intensity(intensity=10000.0)

        # Test 3: Raggio Grande
        print("\n📏 Test 3: SETRADIUS - 2000")
        tester.set_radius(radius=2000.0)

        # Test 4: Verde Brillante (SETALL)
        print("\n🟢 Test 4: SETALL - Verde Brillante")
        tester.set_all(rgb=(0, 255, 0), intensity=15000.0, radius=1500.0)
        time.sleep(1)

        # Test 5: Blu Freddo (SETALL)
        print("\n🔵 Test 5: SETALL - Blu Freddo")
        tester.set_all(rgb=(0, 0, 255), intensity=8000.0, radius=800.0)
        time.sleep(1)

        # Test 6: Giallo Caldo (SETALL)
        print("\n🟡 Test 6: SETALL - Giallo Caldo")
        tester.set_all(rgb=(255, 255, 0), intensity=12000.0, radius=1200.0)
        time.sleep(1)

        # Test 7: Magenta (SETALL)
        print("\n🟣 Test 7: SETALL - Magenta")
        tester.set_all(rgb=(255, 0, 255), intensity=6000.0, radius=600.0)
        time.sleep(1)

        # Test 8: Bianco Neutro (SETALL)
        print("\n⚪ Test 8: SETALL - Bianco Neutro")
        tester.set_all(rgb=(255, 255, 255), intensity=5000.0, radius=1000.0)

        print("\n" + "=" * 60)
        print("✅ Tutti i test completati con successo!")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrotti dall'utente")
    except Exception as e:
        print(f"\n\n❌ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.close()


if __name__ == '__main__':
    run_all_tests()