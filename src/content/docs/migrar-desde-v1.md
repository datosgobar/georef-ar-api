---
title: "Migrar desde v1.0"
description: "Cambios entre la v1.0 y la v2.1 de la API Georef, con ejemplos antes y después."
---

La v1.0 de la API está deprecada. Esta guía resume qué cambia al pasar a la v2.1. Todos los ejemplos se probaron contra la API en vivo el 25 de septiembre de 2026. La documentación de la v1.0 quedó archivada en [/georef-ar-api/v1/](/georef-ar-api/v1/).

:::caution[La URL sin versión sigue siendo v1.0]
`https://apis.datos.gob.ar/georef/api/` (sin versión) **todavía responde con la v1.0**. Para migrar, cambiá tu URL base a `https://apis.datos.gob.ar/georef/api/v2.1/` de forma explícita.
:::

## Resumen de cambios

| Tema | v1.0 | v2.1 |
| --- | --- | --- |
| URL base | `/georef/api/v1.0/` (y `/georef/api/`) | `/georef/api/v2.1/` |
| Municipios | Recurso `/municipios` | `/municipios` deprecado; usá `/gobiernos-locales` |
| Parámetro `municipio` | Existe (filtro en localidades, asentamientos, etc.) | Eliminado: devuelve error 400 con `codigo_interno` 1000. Usá `gobierno_local` |
| Campo de respuesta `municipio` | Presente | Reemplazado por `gobierno_local` |
| `interseccion=municipio:...` | Válido | Error 400. Usá `interseccion=gobierno_local:...` |
| Recursos nuevos | — | `aglomerados`, `fracciones-censales`, `radios-censales`, `gobiernos-locales`, `cuadras`, `establecimientos`, `establecimientos-cercanos`, `establecimientos-educativos`, `instituciones-universitarias` |
| IDs de calles | 13 dígitos | 15 dígitos |
| IDs de cuadras | — | 22 dígitos |
| IDs de localidades | 8 o 10 dígitos | 8 o 10 dígitos (sin cambios respecto de la última revisión de v1.0) |
| IDs de asentamientos | 8 o 10 caracteres alfanuméricos (ej. `14098A77`) | Igual |
| Localidades censales de CABA | Una sola (`02000010`) | Una por comuna (ej. `02007010`, "CABA - Comuna 1") |
| Centroides | Hasta 13 decimales | 9 decimales |
| Formatos | `json`, `csv`, `geojson`, `shp`, `xml` | Se suma `gpkg` (GeoPackage) |
| `/direcciones` | — | Nuevo campo de respuesta `localidad` y parámetro `desplazar`; los resultados pueden cambiar |
| `/ubicacion` | Provincia, departamento, municipio | Parámetro `division` (`politica` o `geoestadistica`); `campos=completo` suma calle y `nomenclatura` |
| Filtro `categoria` | Solo en `/calles` | También en `/gobiernos-locales`, `/asentamientos`, `/localidades` y establecimientos |
| `/localidades` | Subconjunto de BAHRA | Aplica siempre `categoria="Localidad simple,Componente de localidad compuesta,entidad"` |
| `max` / `max + inicio` | Hasta 5000 / 10000 | Sin cambios |
| Cuota diaria (encabezado `x-ratelimit-limit-day`) | 3.000.000 | 10.000 (además 40 por minuto) |
| Descarga completa | `.json`, `.csv`, `.geojson`, `.ndjson`; redirige a `https://infra.datos.gob.ar/georef/` | Suma las entidades nuevas; redirige a una URL provisoria sin HTTPS (ver [Descarga de base completa](/georef-ar-api/download/)) |

En la v2.1, `/establecimientos-educativos` e `/instituciones-universitarias` también responden con `deprecation: true` y apuntan a `/establecimientos` como reemplazo.

La v2.0 sigue publicada en `/georef/api/v2.0/` y es casi igual a la v2.1: la única diferencia es que la v2.1 agrega el recurso `/establecimientos`.

## Ejemplos antes y después

### De `municipios` a `gobiernos-locales`

Antes (v1.0):

`GET` [`https://apis.datos.gob.ar/georef/api/v1.0/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/v1.0/ubicacion?lat=-27.2741&lon=-66.7529)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "departamento": { "id": "10035", "nombre": "Belén" },
        "lat": -27.2741,
        "lon": -66.7529,
        "municipio": { "id": "100077", "nombre": "Hualfin" },
        "provincia": { "id": "10", "nombre": "Catamarca" }
    }
}
```

Después (v2.1):

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "departamento": { "id": "10035", "nombre": "Belén" },
        "gobierno_local": { "id": "100077", "nombre": "Hualfín" },
        "lat": -27.2741,
        "lon": -66.7529,
        "provincia": { "id": "10", "nombre": "Catamarca" }
    }
}
```

Si seguís llamando a `/v2.1/municipios`, la API responde, pero agrega estos encabezados y filtra implícitamente por `categoria=Municipio`:

```
deprecation: true
link: </api/v2.1/gobiernos-locales>; rel="successor-version"
```

Pasá a [`/gobiernos-locales`](/georef-ar-api/gobiernos-locales/): incluye municipios, comunas, comisiones de fomento y otras categorías.

### El parámetro `municipio` ya no existe

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?municipio=chaco`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?municipio=chaco)

```json
{
    "errores": [
        {
            "ayuda": ["formato", "id", "nombre", "interseccion", "provincia", "orden", "aplanar", "campos", "max", "inicio", "exacto", "categoria"],
            "codigo_interno": 1000,
            "mensaje": "El parámetro especificado no existe. Los parámetros aceptados están listados bajo la clave 'ayuda'.",
            "nombre_parametro": "municipio",
            "ubicacion": "querystring"
        }
    ]
}
```

Donde usabas `municipio=...`, usá `gobierno_local=...` (en `/localidades`, `/asentamientos` y `/localidades-censales`), o `interseccion=gobierno_local:...` en los recursos que aceptan intersección.

### IDs de calles y campo `localidad` en direcciones

Antes (v1.0):

`GET` [`https://apis.datos.gob.ar/georef/api/v1.0/direcciones?departamento=merlo&direccion=Florida al 2950`](https://apis.datos.gob.ar/georef/api/v1.0/direcciones?departamento=merlo&direccion=Florida%20al%202950)

```json
{
    "cantidad": 1,
    "direcciones": [
        {
            "calle": { "categoria": "CALLE", "id": "0653901003490", "nombre": "FLORIDA" },
            "localidad_censal": { "id": "06539010", "nombre": "Merlo" },
            "nomenclatura": "FLORIDA 2950, Merlo, Buenos Aires",
            "ubicacion": { "lat": -34.714091578802766, "lon": -58.73469996603733 },
            ...
        }
    ],
    "total": 1,
    ...
}
```

Después (v2.1):

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/direcciones?departamento=merlo&direccion=Florida al 2950`](https://apis.datos.gob.ar/georef/api/v2.1/direcciones?departamento=merlo&direccion=Florida%20al%202950)

```json
{
    "cantidad": 1,
    "direcciones": [
        {
            "calle": { "categoria": "CALLE", "id": "065390100003490", "nombre": "FLORIDA" },
            "localidad": { "id": null, "nombre": null },
            "localidad_censal": { "id": "06539010", "nombre": "Merlo" },
            "nomenclatura": "FLORIDA 2950, Merlo, Merlo, Buenos Aires",
            "ubicacion": { "lat": -34.71409157867347, "lon": -58.734699966 },
            ...
        }
    ],
    "total": 4,
    ...
}
```

Fijate que cambian el largo del ID de la calle, el formato de `nomenclatura` (ahora incluye la localidad censal) y el `total`. Si guardaste IDs de calles de la v1.0, volvé a normalizar esos datos: no hay una conversión documentada entre los IDs de 13 y de 15 dígitos.

### Centroides

Antes (v1.0): [`/v1.0/provincias?id=86`](https://apis.datos.gob.ar/georef/api/v1.0/provincias?id=86)

```json
"centroide": { "lat": -27.7834318817521, "lon": -63.2526268856462 }
```

Después (v2.1): [`/v2.1/provincias?id=86`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?id=86)

```json
"centroide": { "lat": -27.783431882, "lon": -63.252626886 }
```

## Lista de control

1. Cambiá la URL base a `/georef/api/v2.1/`.
2. Reemplazá `/municipios` por `/gobiernos-locales`, el parámetro `municipio` por `gobierno_local` y `interseccion=municipio:` por `interseccion=gobierno_local:`.
3. Leé el campo `gobierno_local` en lugar de `municipio` en las respuestas (con `aplanar`: `gobierno_local_id`, `gobierno_local_nombre`).
4. Revisá validaciones de largo de IDs (calles de 15 dígitos, cuadras de 22).
5. Revisá tu volumen de pedidos contra la nueva cuota y pasá a [consultas por lotes](/georef-ar-api/bulk/) si hace falta.
6. Si guardaste resultados de `/direcciones` o IDs de calles, volvé a normalizarlos.
