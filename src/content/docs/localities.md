---
title: "Localidades y asentamientos"
---

Entre las entidades que maneja la API hay tres que se suelen confundir: las **localidades censales**, las **localidades** y los **asentamientos**. Esta página explica qué es cada una.

## Localidades censales

Las **localidades censales** son unidades geoestadísticas que arma el [INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-Codgeo) para los censos nacionales. Sus IDs tienen 8 dígitos.

En la v2.1, la Ciudad Autónoma de Buenos Aires tiene una localidad censal por comuna (por ejemplo, `02007010`, "CABA - Comuna 1"). Ver [Comunas de CABA](/georef-ar-api/communes/).

Recurso: [`/localidades-censales`](https://apis.datos.gob.ar/georef/api/v2.1/localidades-censales).

## Asentamientos

Los **asentamientos** provienen de la Base de Asentamientos Humanos de la República Argentina ([BAHRA](http://www.bahra.gob.ar/)), que identifica localidades, parajes y sitios edificados con un nombre y un código único. El listado de asentamientos incluye **toda** la base, así que también contiene entidades que normalmente no llamarías "localidad", como parajes o bases antárticas.

Cada asentamiento tiene una `categoria` (por ejemplo "Localidad simple", "Componente de localidad compuesta", "Entidad", "Paraje" o "Base Antártica") y podés filtrar por ella con el parámetro `categoria`. Los IDs tienen 8 o 10 caracteres y pueden ser alfanuméricos, como `14098A77` o `66105A37`.

Los asentamientos **pueden o no** pertenecer a una localidad censal.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/asentamientos?categoria=Paraje&provincia=salta&max=1&campos=id,nombre,categoria`](https://apis.datos.gob.ar/georef/api/v2.1/asentamientos?categoria=Paraje&provincia=salta&max=1&campos=id,nombre,categoria)

```json
{
    "asentamientos": [
        {
            "categoria": "Paraje",
            "id": "66105A37",
            "nombre": "Taca Taca"
        }
    ],
    "cantidad": 1,
    "inicio": 0,
    "parametros": { ... },
    "total": 626
}
```

Recurso: [`/asentamientos`](https://apis.datos.gob.ar/georef/api/v2.1/asentamientos).

## Localidades

Las **localidades** (no confundir con las localidades censales) son un **subconjunto de los asentamientos de BAHRA**: el que mejor representa el concepto general de "localidad", que no tiene una definición formal.

En la v2.1 ese subconjunto se define por categoría: `/localidades` aplica siempre el filtro `categoria="Localidad simple,Componente de localidad compuesta,entidad"`, y lo vas a ver en el campo `parametros` de la respuesta aunque no lo pidas. Los IDs de las localidades son numéricos, de 8 o 10 dígitos (por ejemplo `10035070` o `0204901001`).

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/localidades?provincia=02&max=3&campos=id,nombre,categoria`](https://apis.datos.gob.ar/georef/api/v2.1/localidades?provincia=02&max=3&campos=id,nombre,categoria)

```json
{
    "cantidad": 3,
    "inicio": 0,
    "localidades": [
        {
            "categoria": "Componente de localidad compuesta",
            "id": "02014010",
            "nombre": "Ciudad de Buenos Aires"
        },
        {
            "categoria": "Entidad",
            "id": "0204901001",
            "nombre": "Flores"
        },
        {
            "categoria": "Entidad",
            "id": "0204901002",
            "nombre": "Parque Chacabuco"
        }
    ],
    "parametros": {
        "campos": ["id", "categoria", "nombre"],
        "categoria": "Localidad simple,Componente de localidad compuesta,entidad",
        "max": 3,
        "provincia": ["02"]
    },
    "total": 49
}
```

Recurso: [`/localidades`](https://apis.datos.gob.ar/georef/api/v2.1/localidades).
