---
title: "Entidades censales y establecimientos"
description: "Aglomerados, fracciones y radios censales, cuadras y establecimientos en la API Georef v2.1."
---

La v2 sumó recursos nuevos. Esta página cuenta qué es cada uno y muestra un ejemplo. Los parámetros completos están en la [referencia de la API](/georef-ar-api/referencia/).

## Unidades geoestadísticas del INDEC

Son las divisiones que usa el INDEC para organizar los censos. La fuente que informa la API es "INDEC". También podés obtener las que contienen un punto con [`/ubicacion?division=geoestadistica`](/georef-ar-api/geom-operations/#recurso-ubicacion).

### Aglomerados

Conjuntos de localidades que forman una misma mancha urbana, como el Gran Rosario. ID de 4 dígitos.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/aglomerados?nombre=rosario`](https://apis.datos.gob.ar/georef/api/v2.1/aglomerados?nombre=rosario)

```json
{
    "aglomerados": [
        {
            "centroide": {
                "lat": -32.918187811,
                "lon": -60.714586922
            },
            "id": "0003",
            "nombre": "Gran Rosario"
        }
    ],
    "cantidad": 1,
    "inicio": 0,
    "parametros": { ... },
    "total": 1
}
```

### Fracciones censales

Subdivisiones de un departamento. No tienen nombre, solo ID de 7 dígitos (provincia + departamento + fracción). Podés filtrarlas por `provincia` y `departamento`.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/fracciones-censales?departamento=02007&max=2`](https://apis.datos.gob.ar/georef/api/v2.1/fracciones-censales?departamento=02007&max=2)

```json
{
    "cantidad": 2,
    "fracciones_censales": [
        {
            "centroide": {
                "lat": -34.620040188,
                "lon": -58.384389813
            },
            "departamento": { "id": "02007", "nombre": "Comuna 1" },
            "id": "0200721",
            "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" }
        },
        { ... } // 1 resultado omitido
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 30
}
```

### Radios censales

Subdivisiones de una fracción censal: la unidad más chica que publica la API. ID de 9 dígitos (fracción + radio). Además de `provincia` y `departamento`, aceptan el filtro `fraccion_censal`.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/radios-censales?departamento=02007&max=2`](https://apis.datos.gob.ar/georef/api/v2.1/radios-censales?departamento=02007&max=2)

```json
{
    "cantidad": 2,
    "inicio": 0,
    "parametros": { ... },
    "radios_censales": [
        {
            "centroide": {
                "lat": -34.581491652,
                "lon": -58.384646536
            },
            "departamento": { "id": "02007", "nombre": "Comuna 1" },
            "id": "020070304",
            "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" }
        },
        { ... } // 1 resultado omitido
    ],
    "total": 352
}
```

## Cuadras

Tramos de calle entre dos esquinas, con el rango de alturas de cada lado. El ID tiene 22 dígitos: los primeros 15 son el ID de la calle. Con `calle` (ID de calle) y `altura` encontrás la cuadra que contiene un número. `/cuadras` no acepta `formato=geojson`.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/cuadras?calle=140140100002460&altura=260&campos=completo`](https://apis.datos.gob.ar/georef/api/v2.1/cuadras?calle=140140100002460&altura=260&campos=completo)

```json
{
    "cantidad": 1,
    "cuadras": [
        {
            "altura": {
                "fin": { "derecha": 298, "izquierda": 299 },
                "inicio": { "derecha": 200, "izquierda": 201 }
            },
            "calle": {
                "id": "140140100002460",
                "nombre": "AV SANTA FE"
            },
            "id": "1401401000024603173361"
        }
    ],
    "parametros": { ... },
    "total": 1
}
```

## Establecimientos

Establecimientos educativos (fuente: Mapa Educativo Nacional) e instituciones universitarias.

- `/establecimientos` (nuevo en la v2.1): busca en los dos tipos a la vez. Con `tipo=educativos` o `tipo=universitarios` te quedás con uno. También filtra por `nombre`, `provincia`, `departamento`, `gestion` y `categoria`. ID de 8 o 9 dígitos.
- `/establecimientos-educativos` e `/instituciones-universitarias`: siguen funcionando, pero están **deprecados** (encabezado `deprecation: true`, con `/establecimientos` como reemplazo).
- `/establecimientos-cercanos`: devuelve los establecimientos a menos de `distancia` metros de un punto (`lat`, `lon`), ordenados por distancia. `distancia` va de 10 a 500000 (por defecto 1000). Solo acepta `GET`.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/establecimientos?nombre=nacional buenos aires&max=2`](https://apis.datos.gob.ar/georef/api/v2.1/establecimientos?nombre=nacional%20buenos%20aires&max=2)

```json
{
    "cantidad": 2,
    "establecimientos": [
        {
            "centroide": {
                "lat": -34.610963822,
                "lon": -58.37363711
            },
            "departamento": { "id": "02007", "nombre": "Comuna 1" },
            "domicilio": "BOLIVAR 263 MONTSERRAT",
            "id": "029000500",
            "nombre": "COLEGIO NACIONAL DE BUENOS AIRES",
            "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" },
            "tipo_establecimiento": "establecimientos_educativos"
        },
        { ... } // 1 resultado omitido
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 2
}
```

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/establecimientos-cercanos?lat=-34.5997&lon=-58.3731&tipo=universitarios&distancia=500&max=2`](https://apis.datos.gob.ar/georef/api/v2.1/establecimientos-cercanos?lat=-34.5997&lon=-58.3731&tipo=universitarios&distancia=500&max=2)

```json
{
    "cantidad": 2,
    "establecimientos_cercanos": [
        {
            "centroide": {
                "lat": -34.599829,
                "lon": -58.37301
            },
            "distancia": 16.54,
            "domicilio": "Viamonte 430",
            "id": "70200919",
            "nombre": "Rectorado - Universidad de Buenos Aires",
            "tipo_establecimiento": "instituciones_universitarias"
        },
        { ... } // 1 resultado omitido
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 2
}
```
