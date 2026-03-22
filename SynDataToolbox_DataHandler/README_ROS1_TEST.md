# Test Comunicazione Unreal Engine ↔ ROS1
## SynDataToolbox — Guida al Test ROS Bridge

> ✅ Guida verificata e testata su Windows 11 + WSL2 Ubuntu 20.04 + ROS Noetic

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

### Verifica se WSL2 è già installato

Apri **PowerShell** e digita:

```powershell
wsl --list --verbose
```

- Se vedi `Ubuntu-20.04` con `VERSION 2` → passa direttamente al **punto 2**
- Se vedi solo `docker-desktop` → devi installare Ubuntu 20.04
- Se il comando non esiste → devi installare WSL2

### Installazione WSL2 (solo se non presente)

Apri **PowerShell come Amministratore**:

```powershell
# Installa WSL2
wsl --install

# Riavvia il PC, poi installa Ubuntu 20.04
wsl --install -d Ubuntu-20.04
```

Al primo avvio di Ubuntu ti verrà chiesto di creare **username** e **password**.

### Aprire un terminale Ubuntu

- **Windows Terminal**: clicca `▼` → seleziona `Ubuntu-20.04`
- **Da PowerShell/CMD**: digita `wsl`
- **Da menu Start**: cerca `Ubuntu` e aprilo

---

## 2. Installazione ROS Noetic in WSL2

Apri il terminale **Ubuntu 20.04** ed esegui i comandi nell'ordine:

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

### Verifica installazione ROS

```bash
roscore
```

Se parte senza errori → ROS è installato correttamente. Premi `Ctrl+C` per fermarlo.

> ⚠️ Se vedi `roscore cannot run as another roscore/master is already running` significa che
> ROS Master è già attivo — non serve avviarlo di nuovo, puoi procedere direttamente.

---

## 3. Installazione SynDataToolbox in WSL2

```bash
# Vai alla cartella del progetto (accessibile da WSL2 tramite /mnt/c/)
cd /mnt/c/Users/<TUO_USERNAME>/PycharmProjects/UE5/SynDataToolbox_DataHandler

# Aggiorna pip e numpy (necessario per compatibilità)
pip3 install --upgrade pip
pip3 install --upgrade numpy

# Installa il pacchetto
pip3 install -e .

# Installa dipendenze ROS Python
pip3 install rospkg catkin_pkg
```

> ⚠️ Sostituisci `<TUO_USERNAME>` con il tuo nome utente Windows (es. `Andromeda`)

### Verifica numpy

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

Dovresti vedere `1.24.4` o superiore.

---

## 4. Trovare l'IP di Windows da WSL2

> ⚠️ **IMPORTANTE**: WSL2 usa un IP separato da Windows. `localhost` in WSL2
> punta a Linux, non a Windows. Per raggiungere Unreal Engine (che gira su Windows)
> devi usare l'IP del gateway WSL2.

In WSL2, esegui:

```bash
ip route | grep default
```

Output esempio:
```
default via 172.17.192.1 dev eth0 proto kernel
```

L'IP che precede `dev eth0` (es. `172.17.192.1`) è l'IP di Windows visto da WSL2.

### Verifica che la porta 9734 sia raggiungibile

Con Unreal Engine in **PLAY**, esegui:

```bash
nc -zv 172.17.192.1 9734
```

Output atteso:
```
Connection to 172.17.192.1 9734 port [tcp/*] succeeded!
```

### Imposta la variabile d'ambiente (consigliato)

```bash
# Aggiungi al .bashrc per renderlo permanente
echo "export UE_HOST=172.17.192.1" >> ~/.bashrc
source ~/.bashrc
```

> ⚠️ L'IP di Windows può cambiare ad ogni riavvio di WSL2.
> Se la connessione smette di funzionare, riesegui `ip route | grep default`
> e aggiorna `UE_HOST`.

---

## 5. Preparazione Unreal Engine

1. Apri il progetto Unreal Engine su **Windows**
2. Assicurati che il plugin **SynDataToolbox** sia abilitato:
   - *Edit → Plugins → cerca "SynDataToolbox" → abilita*
3. Verifica che nella scena siano presenti:
   - Un attore **CameraSDT** (sensore RGB)
   - Un attore **CoordinateActionManager** (per le coordinate PoI)
4. Premi **Play** per avviare la simulazione
5. Verifica nei log di UE5 la riga:
   ```
   LogTemp: Warning: Server waiting on 0.0.0.0:9734
   ```

> ⚠️ Il `test_ros_bridge` e il `main.py` **non possono girare contemporaneamente**
> sulla stessa porta 9734. Ferma il `main.py` prima di avviare il test bridge.

---

## 6. Eseguire il Test

Apri **3 terminali Ubuntu** separati.

### Terminale 1 — Avvia roscore

```bash
source /opt/ros/noetic/setup.bash
roscore
```

Lascia questo terminale aperto per tutta la durata del test.

### Terminale 2 — Avvia il test bridge

```bash
cd /mnt/c/Users/<TUO_USERNAME>/PycharmProjects/UE5/SynDataToolbox_DataHandler
source /opt/ros/noetic/setup.bash
python3 -m syndatatoolbox_api.test.test_ros_bridge --host 172.17.192.1
```

Oppure, se hai impostato `UE_HOST` nel `.bashrc`:

```bash
python3 -m syndatatoolbox_api.test.test_ros_bridge
```

### Output atteso nel Terminale 2

```
============================================================
  TEST ROSBridge — SynDataToolbox ↔ ROS1
============================================================
  🎯 Target: 172.17.192.1:9734
============================================================
✅ rospy importato correttamente
✅ cv_bridge importato correttamente
✅ numpy disponibile
------------------------------------------------------------
📡 Connessione a Unreal Engine su 172.17.192.1:9734 ...
   (Assicurati che UE5 sia in PLAY)

Available action managers:
-------------------------
	CoordinateActionManager(CoordinateActionManagerSDT)
	LightControlActionManager(LightControlActionManagerSDT)
Available sensors:
-------------------------
	RGBCamera(CameraSDT)

✅ Connesso a Unreal Engine!
------------------------------------------------------------
📋 Oggetti disponibili in UE5:
   Sensors:         ['RGBCamera(CameraSDT)']
   Action Managers: ['CoordinateActionManager(...)', 'LightControlActionManager(...)']
------------------------------------------------------------
🎥 Sensore RGB trovato: 'RGBCamera(CameraSDT)'
📍 CoordinateActionManager trovato: 'CoordinateActionManager(CoordinateActionManagerSDT)'
------------------------------------------------------------
[INFO] [ROSBridge] Nodo 'syndatatoolbox_test_bridge' avviato.
[INFO] [ROSBridge] Publisher pronti su '/syndatatoolbox/*'
✅ ROSBridge inizializzato!
------------------------------------------------------------
📸 Test pubblicazione singolo frame RGB...
✅ Frame pubblicato! Shape: (1080, 1920, 3), Range: [0.000, 0.957]
📍 Test pubblicazione PoI...
✅ PoI pubblicato!
------------------------------------------------------------
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

## 7. Topic ROS Pubblicati

| Topic | Tipo | Descrizione |
|---|---|---|
| `/syndatatoolbox/camera/rgb` | `sensor_msgs/Image` | Frame RGB dalla camera UE5 |
| `/syndatatoolbox/camera/info` | `sensor_msgs/CameraInfo` | Parametri intrinseci camera |
| `/syndatatoolbox/poi/position` | `geometry_msgs/PointStamped` | Coordinate PoI (metri) |
| `/syndatatoolbox/poi/pose` | `geometry_msgs/PoseStamped` | Posa completa PoI |
| `/syndatatoolbox/status` | `std_msgs/String` | Stato del bridge (RUNNING/STOPPED) |

> ℹ️ Le coordinate vengono convertite automaticamente da **centimetri (UE5)** a **metri (ROS)**
> e l'asse Y viene invertito per rispettare il sistema di riferimento ROS (destrorso).

---

## 8. Visualizzazione con rqt (opzionale)

Per visualizzare le immagini in tempo reale:

```bash
sudo apt install ros-noetic-rqt-image-view -y
rqt_image_view /syndatatoolbox/camera/rgb
```

---

## 9. Architettura della Comunicazione

```
Windows                               WSL2 (Ubuntu 20.04)
┌──────────────────────────┐          ┌───────────────────────────────┐
│     Unreal Engine 5      │          │          ROS Noetic           │
│                          │          │                               │
│   SynDataToolbox         │  TCP     │   test_ros_bridge.py          │
│   Plugin (C++)           │◄────────►│   --host 172.17.192.1:9734    │
│                          │          │              │                │
│   - CameraSDT            │          │         ROSBridge             │
│   - CoordinateActionMgr  │          │              │                │
│   - LightControlActionMgr│          │      rospy Publisher          │
│   - APIGateway (TCP)     │          │              │                │
└──────────────────────────┘          │   /syndatatoolbox/camera/rgb  │
         porta 9734                   │   /syndatatoolbox/poi/position│
                                      │   /syndatatoolbox/status      │
                                      └───────────────────────────────┘
```

---

## 10. Risoluzione Problemi

### `Connection refused` sulla porta 9734
- Verifica che Unreal Engine sia in **PLAY**
- Verifica il log UE5: deve comparire `Server waiting on 0.0.0.0:9734`
- Il `test_ros_bridge` e il `main.py` **non possono girare contemporaneamente** — ferma il `main.py` prima

### `localhost` non funziona da WSL2
- WSL2 usa un IP separato da Windows — usa l'IP del gateway:
  ```bash
  ip route | grep default   # trova l'IP, es. 172.17.192.1
  python3 -m syndatatoolbox_api.test.test_ros_bridge --host 172.17.192.1
  ```

### `roscore cannot run as another roscore/master is already running`
- ROS Master è già attivo — non serve avviarne un altro
- Verifica con `rostopic list` che ROS funzioni correttamente

### `rospy non trovato`
```bash
source /opt/ros/noetic/setup.bash
```

### `cv_bridge non trovato`
```bash
sudo apt install ros-noetic-cv-bridge -y
```

### Le coordinate PoI sono sempre (0, 0, 0)
- Verifica che nella scena ci sia un **CoordinateActionManager**
- Muovi l'attore nella scena mentre UE5 è in Play

### `ResourceWarning: unclosed socket`
- Warning non bloccante, già risolto in `isar_socket.py`
- Assicurati di chiamare `environment.close_connection()` alla fine dello script

### L'IP di Windows è cambiato dopo il riavvio di WSL2
```bash
# Trova il nuovo IP
ip route | grep default

# Aggiorna la variabile d'ambiente
export UE_HOST=<nuovo_ip>

# Per renderlo permanente aggiorna il .bashrc
sed -i "s/export UE_HOST=.*/export UE_HOST=<nuovo_ip>/" ~/.bashrc
source ~/.bashrc
```

---

## 11. Uso Avanzato nel Codice

```python
from syndatatoolbox_api import environment as env_module
from syndatatoolbox_api.ros_bridge import ROSBridge
import os

# L'indirizzo UE5 viene letto dalla variabile d'ambiente UE_HOST
# Da Windows usa 'localhost', da WSL2 usa l'IP del gateway (es. 172.17.192.1)
UE_HOST = os.environ.get('UE_HOST', 'localhost')

# Connetti a UE5
env = env_module.Environment(port=9734, address=UE_HOST)

# Crea il bridge ROS
bridge = ROSBridge(
    environment=env,
    sensor_name='RGBCamera(CameraSDT)',
    node_name='mio_nodo_ros',
    base_topic='/syndatatoolbox',
    publish_poi=True
)

# Loop bloccante a 10 Hz (Ctrl+C per fermare)
bridge.spin(rate_hz=10.0)

# Oppure loop non bloccante in thread separato
t = bridge.spin_async(rate_hz=10.0)
# ... fai altro nel frattempo ...
bridge.stop()
t.join()

env.close_connection()
```

---

## 12. Note per la Tesi

Il bridge ROS1 è implementato come **layer Python** sopra il protocollo ISAR esistente,
senza modifiche al plugin C++ di Unreal Engine. L'architettura è la seguente:

| Layer | Tecnologia | Ruolo |
|---|---|---|
| **Simulazione** | Unreal Engine 5 + SynDataToolbox C++ | Rendering, sensori, attuatori |
| **Protocollo** | ISAR (TCP custom, porta 9734) | Trasporto dati binario |
| **API Python** | `environment.py`, `RGBCamera.py` | Astrazione oggetti UE5 |
| **ROS Bridge** | `ros_bridge.py` + `rospy` | Pubblicazione topic ROS1 |
| **ROS Master** | `roscore` (WSL2) | Coordinamento nodi ROS |

Questo approccio permette di integrare la simulazione UE5 con qualsiasi
robot fisico o software ROS che condivida gli stessi topic standard
(`sensor_msgs/Image`, `geometry_msgs/PointStamped`).
