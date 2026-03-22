"""
test_ros_bridge.py — Test integrazione ROS1
============================================
Verifica che ROSBridge si connetta a UE5 e pubblichi correttamente
su tutti i topic ROS1.

Come usarlo
-----------
1. Avvia roscore:
      roscore

2. Avvia Unreal Engine e premi PLAY

3. In un altro terminale:
      cd SynDataToolbox_DataHandler
      python -m syndatatoolbox_api.test.test_ros_bridge

4. Verifica i topic in un altro terminale:
      rostopic list
      rostopic echo /syndatatoolbox/poi/position
      rostopic hz  /syndatatoolbox/camera/rgb
      rqt_image_view /syndatatoolbox/camera/rgb   (se hai rqt)
"""

import sys
import time
import os
import argparse

# ── Parsing argomenti ─────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Test ROSBridge — SynDataToolbox ↔ ROS1')
parser.add_argument('--host', type=str,
                    default=os.environ.get('UE_HOST', 'localhost'),
                    help='IP di Unreal Engine (default: localhost, da WSL2 usa 172.17.192.1)')
parser.add_argument('--port', type=int, default=9734,
                    help='Porta di Unreal Engine (default: 9734)')
args = parser.parse_args()

UE_HOST = args.host
UE_PORT = args.port

# ── Controlla dipendenze ───────────────────────────────────────────────────
print("=" * 60)
print("  TEST ROSBridge — SynDataToolbox ↔ ROS1")
print("=" * 60)
print(f"  🎯 Target: {UE_HOST}:{UE_PORT}")
print("=" * 60)

# Test import rospy
try:
    import rospy
    print("✅ rospy importato correttamente")
except ImportError:
    print("❌ rospy NON trovato.")
    print("   Assicurati che ROS1 sia installato e che il PYTHONPATH")
    print("   includa /opt/ros/<distro>/lib/python3/dist-packages")
    sys.exit(1)

# Test import cv_bridge
try:
    import cv_bridge
    print("✅ cv_bridge importato correttamente")
except ImportError:
    print("❌ cv_bridge NON trovato.")
    print("   Installa con: sudo apt install ros-<distro>-cv-bridge")
    sys.exit(1)

# Test import numpy
try:
    import numpy as np
    print("✅ numpy disponibile")
except ImportError:
    print("❌ numpy non trovato. Installa con: pip install numpy")
    sys.exit(1)

print("-" * 60)

# ── Connessione a Unreal Engine ────────────────────────────────────────────
print(f"📡 Connessione a Unreal Engine su {UE_HOST}:{UE_PORT} ...")
print("   (Assicurati che UE5 sia in PLAY)")
print()

from syndatatoolbox_api import environment as env_module

setup = {
    'show': False,             # non mostrare finestra OpenCV
    'image_folder_path': None,
    'mask_folder_path': None,
    'mask_colorized': 'GRAYSCALE',
    'format_output_mask': '.png',
    'segmentation_video_path': None,
    'bounding_box_file_path': None,
    'bounding_box_print_output': False,
    'video_path': None,
    'render': False
}

try:
    environment = env_module.Environment(port=UE_PORT, address=UE_HOST, setup=setup)
    print("✅ Connesso a Unreal Engine!")
except Exception as e:
    print(f"❌ Impossibile connettersi a UE5: {e}")
    print("   Assicurati che Unreal sia in PLAY e il plugin attivo.")
    sys.exit(1)

# ── Mostra sensori e action managers disponibili ───────────────────────────
print("-" * 60)
print("📋 Oggetti disponibili in UE5:")
print(f"   Sensors:         {list(environment.sensor_set.keys())}")
print(f"   Action Managers: {list(environment.action_manager_set.keys())}")
print("-" * 60)

# ── Individua il nome del sensore RGB ──────────────────────────────────────
sensor_name = None
for name in environment.sensor_set.keys():
    if 'RGBCamera' in name:
        sensor_name = name
        break

if sensor_name is None:
    print("❌ Nessun sensore 'RGBCamera' trovato in UE5.")
    print("   Verifica che la scena contenga un CameraSDT attivo.")
    environment.close_connection()
    sys.exit(1)

print(f"🎥 Sensore RGB trovato: '{sensor_name}'")

# ── Individua il nome del CoordinateActionManager ─────────────────────────
coord_am_name = None
for name in environment.action_manager_set.keys():
    if 'Coordinate' in name:
        coord_am_name = name
        break

if coord_am_name:
    print(f"📍 CoordinateActionManager trovato: '{coord_am_name}'")
else:
    print("⚠️  CoordinateActionManager non trovato — publish_poi disabilitato.")

print("-" * 60)

# ── Test ROSBridge ─────────────────────────────────────────────────────────
print("🔧 Inizializzazione ROSBridge...")
print("   Verifica che 'roscore' sia in esecuzione!")
print()

from syndatatoolbox_api.ros_bridge import ROSBridge

try:
    bridge = ROSBridge(
        environment=environment,
        sensor_name=sensor_name,
        node_name='syndatatoolbox_test_bridge',
        base_topic='/syndatatoolbox',
        publish_poi=(coord_am_name is not None)
    )
    print("✅ ROSBridge inizializzato!")
except RuntimeError as e:
    print(f"❌ ROSBridge non disponibile: {e}")
    environment.close_connection()
    sys.exit(1)
except Exception as e:
    print(f"❌ Errore inizializzazione ROSBridge: {e}")
    environment.close_connection()
    sys.exit(1)

# ── Test pubblicazione singolo frame ──────────────────────────────────────
print("-" * 60)
print("📸 Test pubblicazione singolo frame RGB...")
result = bridge.publish_frame()
if result is not None:
    print(f"✅ Frame pubblicato! Shape: {result.shape}, Range: [{result.min():.3f}, {result.max():.3f}]")
else:
    print("❌ Pubblicazione frame fallita.")

# ── Test pubblicazione PoI ────────────────────────────────────────────────
if coord_am_name:
    print("📍 Test pubblicazione PoI...")
    try:
        bridge.publish_poi()
        print("✅ PoI pubblicato!")
    except Exception as e:
        print(f"⚠️  Errore pubblicazione PoI: {e}")

# ── Riepilogo topic ────────────────────────────────────────────────────────
print("-" * 60)
print("📡 Topic ROS1 attivi:")
print("   /syndatatoolbox/camera/rgb       → sensor_msgs/Image")
print("   /syndatatoolbox/camera/info      → sensor_msgs/CameraInfo")
print("   /syndatatoolbox/poi/position     → geometry_msgs/PointStamped")
print("   /syndatatoolbox/poi/pose         → geometry_msgs/PoseStamped")
print("   /syndatatoolbox/status           → std_msgs/String")
print()
print("🔍 Verifica con:")
print("   rostopic list")
print("   rostopic echo /syndatatoolbox/poi/position")
print("   rostopic hz   /syndatatoolbox/camera/rgb")
print("-" * 60)

# ── Loop continuo ─────────────────────────────────────────────────────────
RATE_HZ = 5.0
print(f"▶  Avvio loop a {RATE_HZ} Hz — premi Ctrl+C per fermare")
print()

try:
    bridge.spin(rate_hz=RATE_HZ)
except KeyboardInterrupt:
    print()
    print("⏹  Stop manuale.")
finally:
    environment.close_connection()
    print("✅ Connessione UE5 chiusa.")
    print("=" * 60)
