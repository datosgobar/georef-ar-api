---
title: "Descarga de base completa"
---

Si necesitás trabajar con todos los datos de la API, lo más práctico es bajar la base completa.

Cada recurso de listado tiene variantes de descarga completa: agregá `.json`, `.csv`, `.geojson` o `.ndjson` al final de la ruta. La API responde con una redirección (HTTP 302) al archivo. Por ejemplo:

- [`https://apis.datos.gob.ar/georef/api/v2.1/provincias.csv`](https://apis.datos.gob.ar/georef/api/v2.1/provincias.csv)
- [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales.geojson`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales.geojson)
- [`https://apis.datos.gob.ar/georef/api/v2.1/localidades.json`](https://apis.datos.gob.ar/georef/api/v2.1/localidades.json)
- [`https://apis.datos.gob.ar/georef/api/v2.1/calles.ndjson`](https://apis.datos.gob.ar/georef/api/v2.1/calles.ndjson)

Hay descargas para: `provincias`, `departamentos`, `aglomerados`, `fracciones-censales`, `radios-censales`, `gobiernos-locales`, `localidades-censales`, `asentamientos`, `localidades`, `calles`, `cuadras`, `establecimientos-educativos` e `instituciones-universitarias`. En la ruta se usa el guion medio, igual que en el recurso (`gobiernos-locales.csv`, no `gobiernos_locales.csv`). No hay descarga completa de `/municipios`, `/establecimientos` ni `/ubicacion`.

:::caution[URL de descarga provisoria]
Al 25 de septiembre de 2026, las descargas de la v2.1 redirigen a `http://181.209.30.107/files/latest/`: una IP, **sin HTTPS**. Tomala como provisoria y no la uses directamente en tus sistemas; pasá siempre por la URL de la API, que va a seguir funcionando si cambia el destino.
:::

Los archivos más grandes son los de calles, cuadras e intersecciones (de cientos de MB a más de 1 GB). Si vas a procesar todo, conviene el formato NDJSON (una entidad por línea), que se puede leer por partes. La estructura de esos archivos está en [Modelo de datos](/georef-ar-api/etl-data/).

El conjunto de datos [Servicio de normalización de direcciones y unidades territoriales de Argentina](https://datos.gob.ar/dataset/servicio-de-normalizacion-de-direcciones-y-unidades-territoriales-de-argentina) del portal de datos abiertos enlaza archivos en `https://infra.datos.gob.ar/georef/` (con HTTPS). Al 25/09/2026, `provincias.ndjson` en ese servidor tiene la misma versión de datos (13.0.0) que la descarga de la v2.1, aunque el catálogo todavía no lista todas las entidades nuevas.
