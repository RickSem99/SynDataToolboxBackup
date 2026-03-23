"""
genera_pdf_tesi.py
Genera il PDF della documentazione architetturale del plugin SynDataToolbox per la tesi.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "SynDataToolbox_Architettura_Tesi.pdf")

# ──────────────────────────────────────────────────────────────────────────────
# COLORI
# ──────────────────────────────────────────────────────────────────────────────
COL_BLU      = colors.HexColor("#1A3C6E")
COL_BLU_MED  = colors.HexColor("#2E6DB4")
COL_BLU_LIGHT= colors.HexColor("#D6E4F7")
COL_GRIGIO   = colors.HexColor("#F5F5F5")
COL_GRIGIO_BD= colors.HexColor("#CCCCCC")
COL_VERDE    = colors.HexColor("#1E7A1E")
COL_ARANCIO  = colors.HexColor("#C0392B")
COL_TESTO    = colors.HexColor("#1A1A1A")
COL_CODE_BG  = colors.HexColor("#F0F0F0")
COL_CODE_BD  = colors.HexColor("#AAAAAA")

# ──────────────────────────────────────────────────────────────────────────────
# STILI
# ──────────────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_styles():
    s = {}

    s['title'] = ParagraphStyle('title',
        fontSize=24, fontName='Helvetica-Bold',
        textColor=COL_BLU, alignment=TA_CENTER,
        spaceAfter=6, leading=30)

    s['subtitle'] = ParagraphStyle('subtitle',
        fontSize=14, fontName='Helvetica',
        textColor=COL_BLU_MED, alignment=TA_CENTER,
        spaceAfter=4, leading=18)

    s['date'] = ParagraphStyle('date',
        fontSize=10, fontName='Helvetica',
        textColor=colors.grey, alignment=TA_CENTER,
        spaceAfter=20)

    s['h1'] = ParagraphStyle('h1',
        fontSize=16, fontName='Helvetica-Bold',
        textColor=COL_BLU, spaceBefore=18, spaceAfter=8,
        leading=20, borderPadding=(0,0,4,0))

    s['h2'] = ParagraphStyle('h2',
        fontSize=13, fontName='Helvetica-Bold',
        textColor=COL_BLU_MED, spaceBefore=12, spaceAfter=6,
        leading=16)

    s['h3'] = ParagraphStyle('h3',
        fontSize=11, fontName='Helvetica-Bold',
        textColor=COL_TESTO, spaceBefore=8, spaceAfter=4,
        leading=14)

    s['body'] = ParagraphStyle('body',
        fontSize=10, fontName='Helvetica',
        textColor=COL_TESTO, alignment=TA_JUSTIFY,
        spaceAfter=6, leading=14)

    s['bullet'] = ParagraphStyle('bullet',
        fontSize=10, fontName='Helvetica',
        textColor=COL_TESTO, leftIndent=16,
        bulletIndent=6, spaceAfter=3, leading=13)

    s['code'] = ParagraphStyle('code',
        fontSize=8, fontName='Courier',
        textColor=colors.HexColor("#1A1A1A"),
        backColor=COL_CODE_BG,
        leftIndent=8, rightIndent=8,
        spaceAfter=2, leading=11,
        borderColor=COL_CODE_BD, borderWidth=0.5,
        borderPadding=4)

    s['code_title'] = ParagraphStyle('code_title',
        fontSize=8, fontName='Courier-Bold',
        textColor=COL_BLU_MED,
        spaceAfter=1, leading=11)

    s['caption'] = ParagraphStyle('caption',
        fontSize=8, fontName='Helvetica-Oblique',
        textColor=colors.grey, alignment=TA_CENTER,
        spaceAfter=8)

    s['note'] = ParagraphStyle('note',
        fontSize=9, fontName='Helvetica-Oblique',
        textColor=colors.HexColor("#555555"),
        backColor=colors.HexColor("#FFFBE6"),
        leftIndent=8, rightIndent=8,
        borderColor=colors.HexColor("#F0C040"),
        borderWidth=0.5, borderPadding=5,
        spaceAfter=8, leading=12)

    return s

S = make_styles()

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: tabella dati
# ──────────────────────────────────────────────────────────────────────────────
def make_table(headers, rows, col_widths=None):
    data = [[Paragraph(f'<b>{h}</b>', S['body']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S['body']) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0),  COL_BLU),
        ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
        ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[COL_GRIGIO, colors.white]),
        ('GRID',        (0,0), (-1,-1), 0.4, COL_GRIGIO_BD),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: blocco diagramma (testo monospace in box colorato)
# ──────────────────────────────────────────────────────────────────────────────
def make_diagram_box(lines, title=None, bg=COL_GRIGIO, border=COL_BLU_MED):
    content = []
    if title:
        content.append(Paragraph(f'<b>{title}</b>', S['code_title']))
    for line in lines:
        line_esc = (line
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))
        content.append(Paragraph(line_esc, S['code']))
    return content

# ──────────────────────────────────────────────────────────────────────────────
# COSTRUZIONE DOCUMENTO
# ──────────────────────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2.5*cm,  bottomMargin=2.5*cm,
        title="SynDataToolbox — Architettura Plugin UE5 + ROS1",
        author="Andromeda"
    )

    story = []

    # ──────────────────────────────────────────────────────────────────────────
    # COPERTINA
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("SynDataToolbox", S['title']))
    story.append(Paragraph("Architettura del Plugin UE5 &amp; Integrazione ROS1", S['subtitle']))
    story.append(Paragraph("Documentazione per Tesi di Laurea — Marzo 2026", S['date']))
    story.append(HRFlowable(width="100%", thickness=2, color=COL_BLU, spaceAfter=20))

    # Tabella riepilogativa copertina
    story.append(make_table(
        ["Componente", "Tecnologia", "Versione"],
        [
            ["Simulatore",       "Unreal Engine",           "5.x"],
            ["Plugin C++",       "SynDataToolbox (ISAR)",   "custom"],
            ["API Python",       "syndatatoolbox_api",      "0.0.2"],
            ["ROS Bridge",       "rospy + cv_bridge",       "Noetic"],
            ["Ambiente ROS",     "Ubuntu (WSL2)",           "20.04"],
            ["Comunicazione",    "TCP Socket (ISAR)",       "porta 9734"],
        ],
        col_widths=[5.5*cm, 7*cm, 4*cm]
    ))

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 1. ARCHITETTURA GERARCHICA
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Architettura del Plugin — Visione Gerarchica", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    story.append(Paragraph(
        "Il plugin <b>SynDataToolbox</b> adotta un'architettura a <b>3 livelli gerarchici</b> "
        "che separano nettamente la simulazione, il trasporto dati e il layer applicativo. "
        "Questa scelta consente di modificare ciascun livello indipendentemente dagli altri.",
        S['body']))

    story.append(Spacer(1, 0.3*cm))

    diag_arch = [
        "┌─────────────────────────────────────────────────────────────┐",
        "│              LAYER 1 — UE5 Engine (C++)                     │",
        "│                                                             │",
        "│   CameraSDT     CoordinateActionManager   LightControlMgr  │",
        "│   (sensore RGB) (posizione camera)        (luci scena)     │",
        "│        │                │                       │          │",
        "│        └────────────────┼───────────────────────┘          │",
        "│                         ▼                                   │",
        "│              ISARServer — TCP Socket 0.0.0.0:9734           │",
        "│              Serializzazione binaria custom                 │",
        "└─────────────────────────┬───────────────────────────────────┘",
        "                          │  TCP / Protocollo ISAR",
        "                          │  porta 9734",
        "┌─────────────────────────▼───────────────────────────────────┐",
        "│              LAYER 2 — Python API Layer                     │",
        "│                                                             │",
        "│   environment.py    RGBCamera.py    CoordinateActionMgr.py │",
        "│   (facade)          (decodifica)    (controllo posizione)  │",
        "│        │                │                       │          │",
        "│        └────────────────┼───────────────────────┘          │",
        "│                         ▼                                   │",
        "│              ros_bridge.py  (Bridge ROS)                    │",
        "│              rospy Publisher → topic ROS1 standard          │",
        "└─────────────────────────┬───────────────────────────────────┘",
        "                          │  rospy publish()",
        "┌─────────────────────────▼───────────────────────────────────┐",
        "│              LAYER 3 — ROS1 Core (WSL2)                     │",
        "│                                                             │",
        "│   roscore (ROS Master)                                      │",
        "│   /syndatatoolbox/camera/rgb     sensor_msgs/Image          │",
        "│   /syndatatoolbox/camera/info    sensor_msgs/CameraInfo     │",
        "│   /syndatatoolbox/poi/position   geometry_msgs/PointStamped │",
        "│   /syndatatoolbox/poi/pose       geometry_msgs/PoseStamped  │",
        "│   /syndatatoolbox/status         std_msgs/String            │",
        "└─────────────────────────────────────────────────────────────┘",
    ]

    story += make_diagram_box(diag_arch, title="Figura 1 — Architettura a 3 Livelli")
    story.append(Paragraph("Figura 1: Architettura gerarchica del plugin SynDataToolbox.", S['caption']))

    # ──────────────────────────────────────────────────────────────────────────
    # 2. IMPLEMENTAZIONE PUBLISHER
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Implementazione del Publisher — Scelta Tecnica", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    story.append(Paragraph(
        "Il publisher ROS <b>non</b> è implementato nel plugin C++ di Unreal Engine. "
        "La scelta progettuale è stata quella di usare un <b>socket TCP custom</b> (protocollo ISAR) "
        "nel C++ e un <b>bridge Python</b> per la pubblicazione su ROS1. "
        "Questa decisione è motivata dalla massima portabilità e dalla totale assenza "
        "di dipendenze ROS nel codice C++.",
        S['body']))

    story.append(Spacer(1, 0.3*cm))

    story.append(make_table(
        ["Approccio", "Usato?", "Motivazione"],
        [
            ["ROSIntegration (plugin UE4/5)", "✗ No",
             "Richiede rosbridge_suite, aggiunge latenza WebSocket"],
            ["rclUE (ROS2 nativo in UE5)",    "✗ No",
             "Richiede ROS2, incompatibile con ROS Noetic target"],
            ["Socket TCP custom (ISAR)",      "✓ Sì",
             "Massima portabilità, zero dipendenze ROS nel C++"],
        ],
        col_widths=[5.5*cm, 2.5*cm, 8.5*cm]
    ))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Flusso del Publisher — step by step:", S['h3']))

    diag_pub = [
        "UE5 C++ (Windows)            Python (Windows/WSL2)        ROS1 (WSL2)",
        "",
        "CaptureComponent2D           RGBCamera.get_frame()        rospy.Publisher",
        "      │                             │                           │",
        "      │  pixel buffer               │  TCP recv()              │",
        "      ▼                             ▼                           │",
        "ISARServer.SendFrame()  ──────► isar_socket.py                 │",
        "   (porta 9734)            deserializza → numpy array          │",
        "                                     │                          │",
        "                                     ▼                          │",
        "                            ros_bridge.py                       │",
        "                        CvBridge.cv2_to_imgmsg()               │",
        "                                     │                          │",
        "                                     └──── publish() ──────────►",
        "                                           /syndatatoolbox/",
        "                                           camera/rgb",
    ]
    story += make_diagram_box(diag_pub, title="Figura 2 — Flusso del Publisher RGB")
    story.append(Paragraph("Figura 2: Flusso dati dalla camera UE5 al topic ROS1.", S['caption']))

    # ──────────────────────────────────────────────────────────────────────────
    # 3. DIAGRAMMA UML DEI COMPONENTI
    # ──────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3. Diagramma UML dei Componenti", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    story.append(Paragraph(
        "Il diagramma seguente illustra i blocchi logici del sistema secondo la notazione "
        "UML Component Diagram. I componenti sono organizzati in tre sottosistemi: "
        "<b>UE5 Engine</b>, <b>Python API Layer</b> e <b>ROS1 Core</b>.",
        S['body']))

    story.append(Spacer(1, 0.3*cm))

    uml = [
        "┌────────────────────────── <<subsystem>> UE5 Engine ──────────────────────────┐",
        "│                                                                               │",
        "│  ┌──────────────────┐  ┌────────────────────────┐  ┌──────────────────────┐ │",
        "│  │   <<component>>  │  │     <<component>>      │  │    <<component>>     │ │",
        "│  │   CameraSDT      │  │ CoordinateActionManager│  │ LightControlAction   │ │",
        "│  │                  │  │                        │  │ Manager              │ │",
        "│  │ +get_frame()     │  │ +set_position(loc,rot) │  │ +set_intensity(v)    │ │",
        "│  │ +get_info()      │  │ +get_position()        │  │ +set_color(r,g,b)    │ │",
        "│  └────────┬─────────┘  └────────────┬───────────┘  └──────────┬───────────┘ │",
        "│           │                          │                         │             │",
        "│           └──────────────────────────┼─────────────────────────┘             │",
        "│                                      ▼                                       │",
        "│                   ┌──────────────────────────────┐                           │",
        "│                   │      <<component>>            │                           │",
        "│                   │      ISARServer               │                           │",
        "│                   │                               │                           │",
        "│                   │  +Listen(port: 9734)          │                           │",
        "│                   │  +Serialize(data: buffer)     │                           │",
        "│                   │  +Deserialize(cmd: string)    │                           │",
        "│                   └──────────────┬───────────────┘                           │",
        "└──────────────────────────────────┼───────────────────────────────────────────┘",
        "                                   │  TCP Socket (ISAR Protocol) porta 9734",
        "┌──────────────────────────────────┼─────────────── <<subsystem>> Python API ──┐",
        "│                                  ▼                                           │",
        "│                   ┌──────────────────────────────┐                           │",
        "│                   │      <<component>>            │                           │",
        "│                   │      environment.py (Facade)  │                           │",
        "│                   │  +connect()                   │                           │",
        "│                   │  +get_sensors()               │                           │",
        "│                   │  +get_action_managers()       │                           │",
        "│                   │  +get_obs(sensor_list)        │                           │",
        "│                   └──────────────┬───────────────┘                           │",
        "│          ┌───────────────────────┼───────────────────────┐                   │",
        "│          ▼                       ▼                       ▼                   │",
        "│  ┌──────────────┐  ┌──────────────────────┐  ┌────────────────────────┐     │",
        "│  │ RGBCamera.py │  │CoordinateAction       │  │LightControlAction      │     │",
        "│  │              │  │Manager.py             │  │Manager.py              │     │",
        "│  │+get_frame()  │  │+set_position()        │  │+set_intensity()        │     │",
        "│  │+decode_buf() │  │+get_position()        │  │+set_color()            │     │",
        "│  └──────┬───────┘  └────────┬──────────────┘  └────────────────────────┘     │",
        "│         └───────────────────┘                                                │",
        "│                             ▼                                                │",
        "│              ┌──────────────────────────────┐                               │",
        "│              │      <<component>>            │                               │",
        "│              │      ros_bridge.py            │                               │",
        "│              │  +publish_frame()             │                               │",
        "│              │  +publish_poi()               │                               │",
        "│              │  +spin(rate_hz)               │                               │",
        "│              │  +spin_async()                │                               │",
        "│              └──────────────┬───────────────┘                               │",
        "└─────────────────────────────┼──────────────────────────────────────────────-┘",
        "                              │  rospy.Publisher",
        "┌─────────────────────────────┼───────────────── <<subsystem>> ROS1 Core ──────┐",
        "│                             ▼                                                │",
        "│              ┌──────────────────────────────┐                               │",
        "│              │   roscore — ROS Master Node   │                               │",
        "│              └──────────────┬───────────────┘                               │",
        "│       ┌──────────┬──────────┼──────────────┬──────────────┐                 │",
        "│       ▼          ▼          ▼               ▼              ▼                 │",
        "│  /camera    /camera/    /poi/           /poi/         /status               │",
        "│  /rgb       info        position        pose                                │",
        "│  Image      CameraInfo  PointStamped    PoseStamped   String                │",
        "│                                                                              │",
        "│  ┌────────────────────────────────────┐                                     │",
        "│  │  <<node>> SLAM / Robot Controller  │  (integrabile)                      │",
        "│  │  subscribes: /camera/rgb            │                                     │",
        "│  │  subscribes: /poi/position          │                                     │",
        "│  └────────────────────────────────────┘                                     │",
        "└──────────────────────────────────────────────────────────────────────────────┘",
    ]
    story += make_diagram_box(uml, title="Figura 3 — UML Component Diagram")
    story.append(Paragraph(
        "Figura 3: Diagramma UML dei componenti — UE5 Engine, Python API Layer e ROS1 Core.",
        S['caption']))

    # ──────────────────────────────────────────────────────────────────────────
    # 4. LOGICA DI STRESS — LUCI E TRAIETTORIE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Logica di Stress — Illuminazione e Traiettorie", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    story.append(Paragraph("4.1 Controllo Procedurale delle Luci", S['h2']))
    story.append(Paragraph(
        "Le luci <b>non</b> sono controllate da Blueprint UE5 ma tramite "
        "<b>comandi ISAR</b> inviati dal layer Python. Il plugin C++ espone il comando "
        "<code>SETLIGHT</code> che modifica a runtime i parametri di intensità, colore "
        "e direzione della luce nella scena. Le configurazioni luce sono definite "
        "staticamente in <b>acquisition_config.ini</b> e iterate in loop per ogni "
        "punto della traiettoria.",
        S['body']))

    story.append(Spacer(1, 0.2*cm))

    code_light = [
        "# Estratto concettuale da LightControlActionManager.py",
        "def set_light_config(self, intensity, color, angle):",
        "    # intensity: 0.0 -> 1.0 (UE5 scala a lux reali)",
        "    # color:     [R, G, B] normalizzato 0.0 -> 1.0",
        "    # angle:     direzione in gradi (DirectionalLight)",
        "    cmd = f'SETLIGHT {intensity} {color[0]} {color[1]} {color[2]} {angle}'",
        "    self._send_command(cmd)   # → TCP ISAR → UE5 C++",
    ]
    story += make_diagram_box(code_light, title="Snippet 1 — Controllo Luce via ISAR")
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.2 Registrazione e Replay della Traiettoria", S['h2']))
    story.append(Paragraph(
        "Le traiettorie <b>non</b> usano Blueprint UE5. Vengono registrate live tramite "
        "input globale Windows (<code>GetAsyncKeyState</code>) e salvate come sequenze "
        "di punti <code>{loc, rot}</code> in JSON. Prima dell'acquisizione vengono "
        "<b>deduplicate geometricamente</b> per eliminare frame identici (soglia: "
        "0.5° di variazione angolare o 1 cm di spostamento).",
        S['body']))

    story.append(Spacer(1, 0.2*cm))

    code_traj = [
        "# Estratto da acquisition_engine.py",
        "def run_acquisition_trajectory(self, trajectory_file, delay):",
        "    with open(trajectory_file) as f:",
        "        points = json.load(f)        # lista {loc:[x,y,z], rot:[p,y,r]}",
        "",
        "    for point in points:",
        "        # 1. Muovi la camera via CoordinateActionManager (ISAR)",
        "        self.coord_manager.set_position(point['loc'], point['rot'])",
        "        time.sleep(delay)",
        "",
        "        # 2. Per ogni config luce → scatta",
        "        for light_config in self.light_configs:",
        "            self.light_manager.set_light_config(**light_config)",
        "            time.sleep(self.stabilization_delay)",
        "            frame = self.camera.get_frame()   # ← TCP ISAR",
        "            self._save_frame(frame, point, light_config)",
    ]
    story += make_diagram_box(code_traj, title="Snippet 2 — Replay Traiettoria + Loop Luce")
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.3 Diagramma di Flusso — Stress-Test Completo", S['h2']))

    diag_flow = [
        "                      main.py",
        "                         │",
        "                         ▼",
        "          ┌──────────────────────────────┐",
        "          │   Registra Traiettoria Live   │",
        "          │   record_trajectory_live()    │",
        "          │   (N punti grezzi)            │",
        "          └──────────────┬───────────────┘",
        "                         │",
        "                         ▼",
        "          ┌──────────────────────────────┐",
        "          │   Deduplicazione Geometrica   │",
        "          │   deduplicate_trajectory()    │",
        "          │   soglia: 0.5° | 1 cm        │",
        "          │   N punti → M punti (M < N)  │",
        "          └──────────────┬───────────────┘",
        "                         │",
        "                         ▼",
        "          ┌──────────────────────────────┐",
        "          │  Carica acquisition_config    │",
        "          │  K configurazioni luce        │",
        "          └──────────────┬───────────────┘",
        "                         │",
        "          ┌──────────────▼───────────────┐",
        "          │  for i, punto in T (M punti):│◄──────────────┐",
        "          │                              │               │",
        "          │    CoordMgr.set_pos(punto)   │               │",
        "          │    → ISAR: SETPOS x y z p y r│               │",
        "          │    sleep(delay)              │               │",
        "          │                              │               │",
        "          │    for j, luce in L (K conf):│◄────────┐     │",
        "          │      LightMgr.set_light(luce)│         │     │",
        "          │      → ISAR: SETLIGHT i r g b│         │     │",
        "          │      sleep(stab_delay)       │         │     │",
        "          │      frame = cam.get_frame() │         │     │",
        "          │      → ISAR: GETFRAME        │         │     │",
        "          │      save(frame, metadata)   │         │     │",
        "          │      → disk: frame_i_j.png   │ j++─────┘     │",
        "          │    end for                   │               │",
        "          │                              │ i++───────────┘",
        "          └──────────────────────────────┘",
        "                         │",
        "                         ▼",
        "          Totale scatti: M × K",
        "          (es. 84 punti × 8 config = 672 scatti)",
    ]
    story += make_diagram_box(diag_flow, title="Figura 4 — Diagramma di Flusso Stress-Test")
    story.append(Paragraph(
        "Figura 4: Flusso di esecuzione completo dello stress-test di acquisizione.",
        S['caption']))

    # ──────────────────────────────────────────────────────────────────────────
    # 5. TABELLA ARCHITETTURA LAYER
    # ──────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Riepilogo Architettura per Layer", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    story.append(make_table(
        ["Layer", "Tecnologia", "Ruolo"],
        [
            ["Simulazione",  "Unreal Engine 5 + SynDataToolbox C++",
             "Rendering, sensori RGB, attuatori luce e posizione"],
            ["Protocollo",   "ISAR (TCP custom, porta 9734)",
             "Trasporto dati binario, serializzazione comandi"],
            ["API Python",   "environment.py, RGBCamera.py",
             "Astrazione oggetti UE5, decodifica frame"],
            ["ROS Bridge",   "ros_bridge.py + rospy",
             "Pubblicazione topic ROS1 standard"],
            ["ROS Master",   "roscore (WSL2 Ubuntu 20.04)",
             "Coordinamento nodi ROS, smistamento topic"],
        ],
        col_widths=[3.5*cm, 5.5*cm, 7.5*cm]
    ))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("5.1 Topic ROS1 Pubblicati", S['h2']))
    story.append(make_table(
        ["Topic", "Tipo ROS", "Descrizione", "Unità"],
        [
            ["/syndatatoolbox/camera/rgb",
             "sensor_msgs/Image",
             "Frame RGB dalla camera UE5",
             "uint8 BGR"],
            ["/syndatatoolbox/camera/info",
             "sensor_msgs/CameraInfo",
             "Parametri intrinseci camera (fx, fy, cx, cy)",
             "pixel"],
            ["/syndatatoolbox/poi/position",
             "geometry_msgs/PointStamped",
             "Coordinate del Punto di Interesse (PoI)",
             "metri"],
            ["/syndatatoolbox/poi/pose",
             "geometry_msgs/PoseStamped",
             "Posa completa PoI (posizione + orientamento)",
             "metri/rad"],
            ["/syndatatoolbox/status",
             "std_msgs/String",
             "Stato del bridge (RUNNING / STOPPED)",
             "—"],
        ],
        col_widths=[5.5*cm, 4.5*cm, 4.5*cm, 2*cm]
    ))

    story.append(Paragraph(
        "⚠ Le coordinate vengono convertite automaticamente da centimetri (UE5) "
        "a metri (ROS) e l'asse Y viene invertito per rispettare il sistema di "
        "riferimento ROS (destrorso) rispetto a quello UE5 (sinistrorso).",
        S['note']))

    # ──────────────────────────────────────────────────────────────────────────
    # 6. CONCLUSIONI
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("6. Conclusioni", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_BLU_LIGHT, spaceAfter=8))

    conclusioni = [
        ("<b>Publisher C++</b>: Non implementato nel C++ — il plugin espone un server "
         "TCP custom (protocollo ISAR). Il bridge ROS è un layer Python che consuma "
         "questo server via rospy."),
        ("<b>ROSIntegration / rclUE</b>: Non utilizzati. La scelta di un socket TCP custom "
         "minimizza le dipendenze e rende il plugin compatibile con qualsiasi versione "
         "di ROS o framework esterno."),
        ("<b>Luci procedurali</b>: Controllate staticamente da acquisition_config.ini "
         "via comandi ISAR. Nessun Blueprint UE5 modificato a runtime — tutto il "
         "controllo avviene dal layer Python."),
        ("<b>Traiettorie</b>: Registrate live da Python con input globale Windows "
         "(GetAsyncKeyState), deduplicate geometricamente (soglia 0.5° / 1 cm), "
         "poi replicate punto per punto via CoordinateActionManager."),
        ("<b>Integrazione ROS</b>: Il bridge ROS1 è un layer aggiuntivo che non "
         "richiede modifiche al plugin C++. Permette di integrare la simulazione UE5 "
         "con qualsiasi robot fisico o software ROS che condivida i topic standard "
         "sensor_msgs/Image e geometry_msgs/PointStamped."),
    ]

    for c in conclusioni:
        story.append(Paragraph(f"• {c}", S['bullet']))
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COL_GRIGIO_BD))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Documento generato automaticamente da SynDataToolbox — Marzo 2026",
        S['caption']))

    # ──────────────────────────────────────────────────────────────────────────
    # BUILD
    # ──────────────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"\n✅ PDF generato con successo!")
    print(f"📄 {OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
