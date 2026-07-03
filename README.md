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

```bash
python src/main.py
```

Presioná `q` para cerrar las ventanas de visualización.

## 🏗️ Estructura del Proyecto

```
golf-sim-vision/
├── config/
│   └── settings.yaml        # Parámetros configurables (cámara, detección, física)
├── src/
│   ├── camera.py            # Captura de video (PS3 Eye)
│   ├── tracker.py           # Detección y seguimiento de la pelota
│   ├── physics.py           # Cálculos de velocidad y ángulo
│   └── main.py              # Punto de entrada
├── tests/                   # Tests unitarios
├── docs/                    # Documentación técnica
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
