---
title: "Condiciones de uso"
---

## Legales

Los datos del Servicio de Normalización de Datos Geográficos de Argentina se publican bajo la licencia [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/deed.es) y los podés usar para cualquier fin, incluso comercial.

## Técnicas

La v2.1 aplica cuotas de uso por cliente. Al 25 de septiembre de 2026, los encabezados de respuesta informan estos límites:

| Encabezado | Límite |
| --- | --- |
| `x-ratelimit-limit-second` | 10 |
| `x-ratelimit-limit-minute` | 40 |
| `x-ratelimit-limit-hour` | 2.000 |
| `x-ratelimit-limit-day` | 10.000 |

Cada respuesta también trae los encabezados `x-ratelimit-remaining-*` con lo que te queda en cada período. Para aprovechar mejor la cuota, usá las [consultas por lotes](/georef-ar-api/bulk/) o la [descarga de la base completa](/georef-ar-api/download/).

Si tu organismo de la Administración Pública Nacional necesita más cuota, escribí a [datosargentina@jefatura.gob.ar](mailto:datosargentina@jefatura.gob.ar). Ver también [Tokens JWT](/georef-ar-api/jwt-token/).
