# Extracción de cuotas de Betano

## ¿Se puede scrapear con Python directo? No.

Betano (lat.betano.com) usa **DataDome** — detección de bots por fingerprint del
navegador y comportamiento, **no por login**. Por eso:

- **Las credenciales NO ayudan.** Estar logueado no pasa DataDome; el bloqueo es
  al request automatizado, no a la cuenta. No necesito un archivo de credenciales.
- `requests` / `curl` / `httpx` reciben un **captcha de DataDome** (se ve en el
  storage: `geo.captcha-delivery.com`). Un scraper Python standalone no funciona.

## Lo que SÍ funciona: extraer del navegador ya abierto

Tu sesión real de Chrome ya pasó DataDome. Dos caminos:

### A) Snippet JS en la consola del navegador (lo que ya hiciste)

Abrís la página del partido, F12 → consola, y corrés un extractor que recorre el
DOM (`document.querySelectorAll` de los bloques-mercado) y arma el JSON. Lo
guardás como `01_data_raw/odds/betano_<partido>_<fecha>.json`.

### B) Chrome MCP (yo tomo control del navegador)

Si me das acceso al Chrome MCP sobre la pestaña abierta, navego, leo el DOM
(`get_page_text` / `read_page`) o intercepto la API de cuotas en
`read_network_requests`, y armo el mismo JSON. No paso por DataDome porque uso tu
sesión real.

## Formato del JSON y parser

El JSON tiene metadatos + un objeto `mercados` con una clave snake_case por
mercado (`resultado_partido`, `goles_totales_mas_menos`, `corners_mas_menos`,
`tarjetas_totales_mas_menos`, `tiros_al_arco`, `goleador`, ...). Cada mercado
trae `nombre`, `tipo` y las cuotas.

El parser **`lib/odds_betano.py`** ingiere ese JSON sin tocar la red:

```python
from lib import odds_betano as OB
data = OB.load("01_data_raw/odds/betano_catar_suiza_2026-06-13.json")
OB.one_x_two(data["mercados"]["resultado_partido"])       # {'home':12, 'draw':5.9, 'away':1.25}
OB.over_under(data["mercados"]["goles_totales_mas_menos"]) # {2.5:{'over':1.65,'under':2.25}, ...}
OB.player_shots(data["mercados"]["tiros_al_arco"])         # {'Breel Embolo': {1:1.17, 2:1.85, ...}}
```

Y `08_models/predict_match.py` cruza todo eso con los modelos y calcula EV.

## Recomendación de arquitectura

No tiene sentido pelear con DataDome. El flujo robusto es:

```
navegador (sesión real) ──JS o Chrome MCP──► JSON en 01_data_raw/odds/
                                                   │
                          lib/odds_betano.py ◄─────┘  (parser, testeable)
                                   │
                          08_models/predict_match.py  (modelo + EV)
```

La pieza Python durable es el **parser + el modelo**, no el scraper. La captura
del JSON queda como un paso semi-manual (snippet) o asistido (Chrome MCP).
