# 🏌️ Golf Sim Vision

Sistema de tracking de pelota de golf por visión artificial para simulador indoor.  
Usa una cámara PS3 Eye a 120fps + proyector para crear una experiencia de simulador vendible.

## 🎯 Qué hace

- Captura video a 120fps con la PS3 Eye (CL-Eye Driver + DirectShow)
- Detecta la pelota de golf en movimiento usando sustracción de fondo
- Calcula velocidad de salida (ball speed) y ángulo de lanzamiento (launch angle)
- Diseñado para integrarse con simuladores (GSPro, E6, o engine propio)

## 📦 Requisitos

- Windows 10/11
- PS3 Eye + [CL-Eye Driver](https://codelaboratories.com/downloads)
- Python 3.10+
- OpenCV 4.x

## 🚀 Instalación

```bash
# Clonar el repo
git clone https://github.com/tu-usuario/golf-sim-vision.git
cd golf-sim-vision

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## ▶️ Uso

### Para el usuario final (modo kiosco)

**Doble click en `INICIAR SIMULADOR.bat`** — eso es todo.

El sistema:
1. Arranca fullscreen en el proyector
2. Si es la primera vez, guía al usuario para calibrar (mostrá el tablero de ajedrez)
3. Muestra pantalla verde "LISTO" cuando puede recibir tiros
4. Detecta el tiro automáticamente → muestra velocidad, ángulo y dirección
5. Vuelve a "LISTO" después de 4 segundos

**Pantallas que ve el usuario:**

| Color | Significado |
|-------|-------------|
| 🟢 Verde | "Podés tirar" |
| 🟡 Amarillo | "Estoy analizando tu tiro..." |
| ⚪ Datos grandes | Resultado: velocidad, ángulo, dirección |
| 🔴 Rojo | Problema (muestra teléfono del técnico) |

**Sonidos:**
- Beep ascendente = "listo para tirar"
- Beep corto = "detecté tu tiro"
- Fanfarria = "buen tiro"
- Beep grave = "problema"

### Para el técnico/developer

```bash
# Modo desarrollo (con consola y ventanas de debug)
python src/main.py

# Calibración manual interactiva
python -m src.calibration.calibrate

# Modo kiosco (fullscreen, sin consola)
pythonw launcher.py
```

### Auto-arranque (que prenda solo con la PC)

1. Click derecho en `INICIAR SIMULADOR.bat` → "Crear acceso directo"
2. Mover el acceso directo a:
   `C:\Users\<usuario>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
3. Listo — la próxima vez que prenda la PC arranca solo

## 🏗️ Estructura del Proyecto

```
golf-sim-vision/
├── INICIAR SIMULADOR.bat     # ← DOBLE CLICK PARA ARRANCAR
├── launcher.py               # Modo kiosco (fullscreen, sin consola)
├── config/
│   ├── settings.yaml         # Parámetros configurables
│   └── calibration.json      # Se genera automático al calibrar
├── src/
│   ├── ui/                   # Pantallas del proyector
│   │   ├── renderer.py       # Motor de renderizado fullscreen
│   │   ├── screens.py        # Pantallas (ready, result, error)
│   │   └── wizard.py         # Wizard de primer uso
│   ├── audio/                # Feedback sonoro (winsound)
│   ├── calibration/          # Calibración con chessboard
│   ├── interfaces/           # Abstracciones (SOLID)
│   ├── camera/               # Captura PS3 Eye
│   ├── detection/            # Detección de pelota (Strategy)
│   ├── tracking/             # Seguimiento temporal
│   ├── physics/              # Cálculos de velocidad/ángulo
│   ├── events/               # Sistema de eventos (Observer)
│   ├── display/              # Visualización debug (OpenCV)
│   ├── factory/              # Factory Pattern
│   ├── pipeline.py           # Pipeline de procesamiento
│   └── main.py               # Entrada modo developer
├── tests/                    # Tests unitarios (29 tests)
├── requirements.txt
└── README.md
```

## 🗺️ Roadmap

### Fase 1 — MVP Tracking (actual)
- [x] Captura 120fps con PS3 Eye
- [x] Detección de movimiento por sustracción de fondo
- [x] Filtrado de contornos por área
- [ ] Cálculo de velocidad (px/frame → m/s con calibración)
- [ ] Detección de ángulo de lanzamiento

### Fase 2 — Precisión
- [ ] Calibración cámara (px → cm reales)
- [ ] Detección de momento de impacto (palo vs pelota)
- [ ] Filtro de Kalman para tracking suave
- [ ] Validación contra radar (si tenés acceso)

### Fase 3 — Integración Simulador
- [ ] Protocolo de comunicación con GSPro (Open Connect API)
- [ ] UI de calibración para el usuario
- [ ] Modo "listo para disparar" con feedback visual

### Fase 4 — Producto Vendible
- [ ] Detección de spin (requiere marcas en pelota o 2da cámara)
- [ ] Instalador / setup wizard
- [ ] Documentación de usuario
- [ ] Hardware kit (cámara + soporte + iluminación)

## 📐 Specs Técnicos

| Parámetro | Valor |
|-----------|-------|
| Cámara | PS3 Eye (OV7720) |
| Resolución | 320x240 @ 120fps |
| Backend | DirectShow (CL-Eye) |
| Detección | MOG2 Background Subtraction |
| Área pelota | 50–1500 px² |

## 📝 Notas

- A 120fps en 320x240 tenés ~8.3ms entre frames. Una pelota de golf a 150mph recorre ~56cm entre frames, así que en la imagen se mueve bastante. El tracking multi-frame es clave.
- La iluminación controlada (LED infrarrojo o blanco constante) mejora muchísimo la detección.

## 📄 Licencia

MIT — Usalo, modificalo, vendelo.
