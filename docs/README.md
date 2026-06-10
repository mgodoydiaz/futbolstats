# `docs/` — Marco teórico y documentación del proyecto

Documentación tipo tesis de investigación que acompaña al pipeline de datos. Está pensada como referencia técnica para entender qué métricas existen, qué datos requieren y cómo se construyen.

## Estructura

```
docs/
├── README.md                    (este archivo)
├── thesis.tex                   (entry point LaTeX, hace \input de cada sección)
├── sections/
│   ├── 00_introduccion.tex      (objetivo, alcance, audiencia)
│   ├── 01_concepto_xg.tex       (xG: definición, cálculo, generalización)
│   ├── 02_catalogo_metricas.tex (catálogo de métricas "expected")
│   ├── 03_fuentes_datos.tex     (qué fuente da qué con qué cobertura)
│   ├── 04_implementacion.tex    (scripts, schemas, pipeline)
│   └── 05_limitaciones.tex      (gaps, sesgos, trabajo futuro)
└── build.ps1                    (compilar a PDF con pdflatex)
```

## Cómo leerlo

Las secciones están pensadas para leerse en orden. Para una lectura rápida (~10 min) podés saltar a:

- **Sección 02** si querés el catálogo de métricas.
- **Sección 03** si querés saber qué fuente usar para qué.
- **Sección 04** si querés saber qué scripts del repo computan qué.

## Cómo compilar a PDF

Necesitás una distribución LaTeX (MiKTeX en Windows, TeX Live en Linux/Mac).

**Opción 1 — script PowerShell**:

```powershell
cd docs
.\build.ps1
```

**Opción 2 — manualmente**:

```powershell
cd docs
pdflatex thesis.tex
pdflatex thesis.tex    # segunda pasada resuelve referencias cruzadas
```

Salida: `docs/thesis.pdf`.

## Si no tenés LaTeX instalado

Los `.tex` son texto plano legible directamente. Las tablas y matemáticas no quedan tan lindas en código fuente, pero el contenido se entiende.

Instalación rápida en Windows:

```powershell
winget install MiKTeX.MiKTeX
```

(después agregar al PATH si winget no lo hace solo).

## Convenciones de notación

| Símbolo | Significado |
|---------|-------------|
| $x_i$ | tiro/evento $i$ |
| $\mathbf{c}_i$ | vector de contexto del evento $i$ |
| $P(\cdot \mid \cdot)$ | probabilidad condicional |
| $\hat{Y}$ | predicción del modelo para $Y$ |
| xG, xA, etc. | métricas "expected" — siempre minúscula la x, mayúscula la inicial |

## Relación con otros documentos del repo

- [`README.md`](../README.md) — overview del proyecto y stack
- [`CLAUDE.md`](../CLAUDE.md) — convenciones técnicas
- [`ROADMAP.md`](../ROADMAP.md) — qué scrapes/análisis falta correr
- `docs/` (este folder) — marco teórico y catálogo de métricas
