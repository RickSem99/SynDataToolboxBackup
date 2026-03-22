"""
ROSBridge — Integrazione ROS1 per SynDataToolbox
=================================================
Pubblica su topic ROS standard i dati acquisiti da Unreal Engine
tramite la connessione ISAR/TCP esistente di Environment.

Topic pubblicati:
  /syndatatoolbox/camera/rgb       → sensor_msgs/Image
  /syndatatoolbox/camera/info      → sensor_msgs/CameraInfo
  /syndatatoolbox/poi/position     → geometry_msgs/PointStamped
  /syndatatoolbox/poi/pose         → geometry_msgs/PoseStamped

Requisiti:
  pip install rospkg catkin_pkg
  (ROS1 installato e roscore in esecuzione)

Utilizzo:
  from syndatatoolbox_api.ros_bridge import ROSBridge
  bridge = ROSBridge(env, sensor_name='RGBCamera(CameraSDT)')
  bridge.spin(rate_hz=10)
"""

import time
import threading
import math

try:
    import rospy
    from sensor_msgs.msg import Image, CameraInfo
    from geometry_msgs.msg import PointStamped, PoseStamped, Point, Quaternion
    from std_msgs.msg import Header, String
    import cv_bridge
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    print("[ROSBridge] ⚠️  ROS1 non trovato. Installa ROS1 e verifica che 'rospy' sia nel PYTHONPATH.")

import numpy as np


class ROSBridge:
    """
    Bridge tra SynDataToolbox (ISAR/TCP) e ROS1.

    Parametri
    ---------
    environment : Environment
        Istanza già connessa a Unreal Engine.
    sensor_name : str
        Nome del sensore RGB da usare (es. 'RGBCamera(CameraSDT)').
    node_name : str
        Nome del nodo ROS da registrare.
    base_topic : str
        Prefisso di tutti i topic pubblicati.
    publish_poi : bool
        Se True, pubblica anche le coordinate PoI.
    """

    def __init__(self,
                 environment,
                 sensor_name: str = 'RGBCamera(CameraSDT)',
                 node_name: str = 'syndatatoolbox_bridge',
                 base_topic: str = '/syndatatoolbox',
                 publish_poi: bool = True):

        if not ROS_AVAILABLE:
            raise RuntimeError(
                "ROS1 non disponibile. Installa ROS1 e verifica che "
                "'rospy' sia nel PYTHONPATH prima di usare ROSBridge."
            )

        self._env = environment
        self._sensor_name = sensor_name
        self._publish_poi = publish_poi
        self._frame_id_camera = 'ue5_camera'
        self._frame_id_world = 'ue5_world'
        self._bridge = cv_bridge.CvBridge()
        self._seq = 0
        self._running = False

        # ── Recupera dimensioni camera dal setup del sensore ──────────────
        try:
            settings_list = environment.get_sensor_settings([sensor_name])
            settings = settings_list[0]
            self._width = settings.get('Width', 1920)
            self._height = settings.get('Height', 1080)
            self._fov = settings.get('FOV', 90)
        except Exception:
            self._width = 1920
            self._height = 1080
            self._fov = 90

        # ── Inizializza nodo ROS ──────────────────────────────────────────
        rospy.init_node(node_name, anonymous=False, disable_signals=False)
        rospy.loginfo(f"[ROSBridge] Nodo '{node_name}' avviato.")

        # ── Publisher ─────────────────────────────────────────────────────
        self._pub_rgb = rospy.Publisher(
            f'{base_topic}/camera/rgb',
            Image,
            queue_size=5
        )
        self._pub_cam_info = rospy.Publisher(
            f'{base_topic}/camera/info',
            CameraInfo,
            queue_size=5
        )
        self._pub_poi_point = rospy.Publisher(
            f'{base_topic}/poi/position',
            PointStamped,
            queue_size=5
        )
        self._pub_poi_pose = rospy.Publisher(
            f'{base_topic}/poi/pose',
            PoseStamped,
            queue_size=5
        )
        self._pub_status = rospy.Publisher(
            f'{base_topic}/status',
            String,
            queue_size=2
        )

        rospy.loginfo(f"[ROSBridge] Publisher pronti su '{base_topic}/*'")

    # ──────────────────────────────────────────────────────────────────────
    # Metodi pubblici
    # ──────────────────────────────────────────────────────────────────────

    def publish_frame(self):
        """
        Acquisisce un frame RGB da UE5 e lo pubblica su ROS.
        Restituisce il numpy array (H, W, 3) o None in caso di errore.
        """
        try:
            obs = self._env.get_obs([self._sensor_name])
            img_array = obs[0]  # float32 (H, W, 3) range [0,1]

            # Converti in uint8 BGR per cv_bridge
            img_bgr = (img_array * 255).astype(np.uint8)

            stamp = rospy.Time.now()
            header = Header(seq=self._seq, stamp=stamp, frame_id=self._frame_id_camera)

            img_msg = self._bridge.cv2_to_imgmsg(img_bgr, encoding='bgr8')
            img_msg.header = header

            self._pub_rgb.publish(img_msg)
            self._pub_cam_info.publish(self._build_camera_info(header))

            self._seq += 1
            return img_array

        except Exception as e:
            rospy.logerr(f"[ROSBridge] Errore publish_frame: {e}")
            return None

    def publish_poi(self):
        """
        Acquisisce le coordinate PoI da UE5 e le pubblica su ROS.
        Converte da centimetri (UE5) a metri (ROS standard).
        """
        if not self._publish_poi:
            return

        try:
            x_cm, y_cm, z_cm = self._env.get_poi_coordinates()

            # UE5 usa sistema sinistrorso con Z=up, ROS usa destrorso con Z=up
            # Conversione: cm → m,  Y UE5 → -Y ROS
            x_m = x_cm / 100.0
            y_m = -y_cm / 100.0   # inversione asse Y
            z_m = z_cm / 100.0

            stamp = rospy.Time.now()
            header = Header(seq=self._seq, stamp=stamp, frame_id=self._frame_id_world)

            # ── PointStamped ──────────────────────────────────────────────
            point_msg = PointStamped()
            point_msg.header = header
            point_msg.point = Point(x=x_m, y=y_m, z=z_m)
            self._pub_poi_point.publish(point_msg)

            # ── PoseStamped (posizione + orientamento neutro) ─────────────
            pose_msg = PoseStamped()
            pose_msg.header = header
            pose_msg.pose.position = Point(x=x_m, y=y_m, z=z_m)
            pose_msg.pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
            self._pub_poi_pose.publish(pose_msg)

        except Exception as e:
            rospy.logerr(f"[ROSBridge] Errore publish_poi: {e}")

    def spin(self, rate_hz: float = 10.0):
        """
        Loop principale bloccante: pubblica frame e PoI a frequenza fissa.
        Termina quando ROS viene spento (Ctrl+C).

        Parametri
        ---------
        rate_hz : float
            Frequenza di pubblicazione in Hz (default 10 Hz).
        """
        rate = rospy.Rate(rate_hz)
        self._running = True
        rospy.loginfo(f"[ROSBridge] ▶ Pubblicazione avviata a {rate_hz} Hz")
        self._pub_status.publish(String(data="RUNNING"))

        try:
            while not rospy.is_shutdown() and self._running:
                self.publish_frame()
                self.publish_poi()
                rate.sleep()

        except rospy.ROSInterruptException:
            pass
        finally:
            self._running = False
            self._pub_status.publish(String(data="STOPPED"))
            rospy.loginfo("[ROSBridge] ⏹ Pubblicazione fermata.")

    def spin_async(self, rate_hz: float = 10.0) -> threading.Thread:
        """
        Avvia il loop di pubblicazione in un thread separato (non bloccante).
        Restituisce il thread avviato.

        Uso:
            t = bridge.spin_async(rate_hz=10)
            # ... fai altro ...
            bridge.stop()
            t.join()
        """
        t = threading.Thread(target=self.spin, args=(rate_hz,), daemon=True)
        t.start()
        rospy.loginfo("[ROSBridge] Thread asincrono avviato.")
        return t

    def stop(self):
        """Ferma il loop di spin_async."""
        self._running = False

    # ──────────────────────────────────────────────────────────────────────
    # Metodi privati / helper
    # ──────────────────────────────────────────────────────────────────────

    def _build_camera_info(self, header: 'Header') -> 'CameraInfo':
        """Costruisce un messaggio CameraInfo con i parametri intrinseci."""
        fx = (self._width / 2.0) / math.tan(math.radians(self._fov / 2.0))
        fy = fx
        cx = self._width / 2.0
        cy = self._height / 2.0

        info = CameraInfo()
        info.header = header
        info.width = self._width
        info.height = self._height
        info.distortion_model = 'plumb_bob'
        info.D = [0.0, 0.0, 0.0, 0.0, 0.0]
        info.K = [fx, 0.0, cx,
                  0.0, fy, cy,
                  0.0, 0.0, 1.0]
        info.R = [1.0, 0.0, 0.0,
                  0.0, 1.0, 0.0,
                  0.0, 0.0, 1.0]
        info.P = [fx, 0.0, cx, 0.0,
                  0.0, fy, cy, 0.0,
                  0.0, 0.0, 1.0, 0.0]
        return info
