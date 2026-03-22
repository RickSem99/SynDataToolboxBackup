# Test Comunicazione Unreal Engine ↔ ROS1
## SynDataToolbox — Guida al Test ROS Bridge

---

## Prerequisiti

| Requisito | Versione |
|---|---|
| Unreal Engine | 5.x |
| Python | 3.8+ |
| ROS | Noetic (Ubuntu 20.04) |
| Windows | 10/11 con WSL2 |

---

## 1. Installazione WSL2 e Ubuntu 20.04

Apri **PowerShell come Amministratore** su Windows:

```powershell
# Installa WSL2
wsl --install

# Riavvia il PC, poi installa Ubuntu 20.04
wsl --install -d Ubuntu-20.04
```

Al primo avvio di Ubuntu ti verrà chiesto di creare **username** e **password**.

---

## 2. Installazione ROS Noetic in WSL2

Apri il terminale **Ubuntu 20.04** ed esegui in ordine:

```bash
# Aggiungi i sorgenti ROS
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt install curl -y
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update

# Installa ROS Noetic
sudo apt install ros-noetic-desktop-full -y

# Installa i pacchetti necessari per il bridge
sudo apt install ros-noetic-cv-bridge -y
sudo apt install ros-noetic-sensor-msgs -y
sudo apt install ros-noetic-geometry-msgs -y
sudo apt install ros-noetic-std-msgs -y
sudo apt install python3-rospy python3-pip -y

# Configura l'ambiente ROS automaticamente ad ogni avvio
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
echo "export ROS_MASTER_URI=http://localhost:11311" >> ~/.bashrc
echo "export ROS_IP=127.0.0.1" >> ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Installazione SynDataToolbox in WSL2

```bash
# Vai alla cartella del progetto (accessibile da WSL2 tramite /mnt/c/)
cd /mnt/c/Users/<TUO_USERNAME>/PycharmProjects/UE5/SynDataToolbox_DataHandler

# Aggiorna pip e numpy
pip3 install --upgrade pip
pip3 install --upgrade numpy

# Installa il pacchetto
pip3 install -e .

# Installa dipendenze ROS Python
pip3 install rospkg catkin_pkg
```

> ⚠️ Sostituisci `<TUO_USERNAME>` con il tuo nome utente Windows (es. `Andromeda`)

---

## 4. Preparazione Unreal Engine

1. Apri il progetto Unreal Engine su **Windows**
2. Assicurati che il plugin **SynDataToolbox** sia abilitato
   - *Edit → Plugins → cerca "SynDataToolbox" → abilita*
3. Verifica che nella scena siano presenti:
   - Un attore **CameraSDT** (sensore RGB)
   - Un attore **CoordinateActionManager** (per le coordinate PoI)
4. Premi **Play** per avviare la simulazione

---

## 5. Eseguire il Test

Apri **3 terminali Ubuntu** separati (usa Windows Terminal → tab Ubuntu):

### Terminale 1 — Avvia roscore
```bash
roscore
```
Lascia questo terminale aperto per tutta la durata del test.

### Terminale 2 — Avvia il test bridge
```bash
cd /mnt/c/Users/<TUO_USERNAME>/PycharmProjects/UE5/SynDataToolbox_DataHandler
source /opt/ros/noetic/setup.bash
python3 -m syndatatoolbox_api.test.test_ros_bridge
```

Output atteso:
```
✅ rospy importato correttamente
✅ cv_bridge importato correttamente
✅ numpy disponibile
✅ Connesso a Unreal Engine!
✅ ROSBridge inizializzato!
✅ Frame pubblicato! Shape: (1080, 1920, 3)
✅ PoI pubblicato!
▶  Avvio loop a 5.0 Hz — premi Ctrl+C per fermare
```

### Terminale 3 — Verifica i topic ROS
```bash
source /opt/ros/noetic/setup.bash

# Lista tutti i topic attivi
rostopic list

# Verifica la frequenza di pubblicazione delle immagini
rostopic hz /syndatatoolbox/camera/rgb

# Verifica le coordinate PoI in tempo reale
rostopic echo /syndatatoolbox/poi/position

# Visualizza info sul topic immagine
rostopic info /syndatatoolbox/camera/rgb
```

---

## 6. Topic ROS Pubblicati

| Topic | Tipo | Descrizione |
|---|---|---|
| `/syndatatoolbox/camera/rgb` | `sensor_msgs/Image` | Frame RGB dalla camera UE5 |
| `/syndatatoolbox/camera/info` | `sensor_msgs/CameraInfo` | Parametri intrinseci camera |
| `/syndatatoolbox/poi/position` | `geometry_msgs/PointStamped` | Coordinate PoI (metri) |
| `/syndatatoolbox/poi/pose` | `geometry_msgs/PoseStamped` | Posa completa PoI |
| `/syndatatoolbox/status` | `std_msgs/String` | Stato del bridge (RUNNING/STOPPED) |

> ℹ️ Le coordinate vengono convertite automaticamente da **centimetri (UE5)** a **metri (ROS)**

---

## 7. Visualizzazione con rqt (opzionale)

Per visualizzare le immagini in tempo reale:

```bash
sudo apt install ros-noetic-rqt-image-view -y
rqt_image_view /syndatatoolbox/camera/rgb
```

---

## 8. Architettura della Comunicazione

```
Windows                          WSL2 (Ubuntu 20.04)
┌─────────────────────┐          ┌──────────────────────────┐
│   Unreal Engine 5   │          │        ROS Noetic         │
│                     │          │                          │
│  SynDataToolbox     │  TCP     │   test_ros_bridge.py     │
│  Plugin (C++)       │◄────────►│   (porta 9734)           │
│                     │ :9734    │          │               │
│  - CameraSDT        │          │   ROSBridge              │
│  - CoordinateAM     │          │          │               │
│  - APIGateway       │          │   rospy Publisher        │
└─────────────────────┘          │          │               │
                                 │   /syndatatoolbox/*      │
                                 │   topic ROS              │
                                 └──────────────────────────┘
```

---

## 9. Risoluzione Problemi

### Errore: `ConnectionRefusedError`
- Verifica che Unreal Engine sia in **PLAY**
- Verifica che il plugin sia abilitato e compilato correttamente

### Errore: `rospy non trovato`
```bash
source /opt/ros/noetic/setup.bash
```

### Errore: `cv_bridge non trovato`
```bash
sudo apt install ros-noetic-cv-bridge -y
```

### Le coordinate PoI sono sempre (0, 0, 0)
- Verifica che nella scena ci sia un **CoordinateActionManager**
- Muovi l'attore nella scena mentre UE5 è in Play

### ResourceWarning: unclosed socket
- È un warning non bloccante, già risolto in `isar_socket.py`
- Se persiste, assicurati di chiamare `environment.close_connection()` alla fine

---

## 10. Uso Avanzato nel Codice

```python
from syndatatoolbox_api import environment as env_module
from syndatatoolbox_api.ros_bridge import ROSBridge

# Connetti a UE5
env = env_module.Environment(port=9734, address='localhost')

# Crea il bridge ROS
bridge = ROSBridge(
    environment=env,
    sensor_name='RGBCamera(CameraSDT)',
    node_name='mio_nodo_ros',
    base_topic='/syndatatoolbox',
    publish_poi=True
)

# Loop bloccante a 10 Hz
bridge.spin(rate_hz=10.0)

# Oppure loop non bloccante (thread separato)
t = bridge.spin_async(rate_hz=10.0)
# ... fai altro ...
bridge.stop()
t.join()

env.close_connection()
```
