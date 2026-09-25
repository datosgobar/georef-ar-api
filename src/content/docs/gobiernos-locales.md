---
title: "Gobiernos locales"
description: "Qué son los gobiernos locales en la API Georef v2.1 y cómo consultarlos."
---

Los **gobiernos locales** son las unidades de gobierno por debajo de la provincia: municipios, comunas, comisiones de fomento, comisiones municipales, juntas de gobierno y comunas rurales, según cómo organice cada provincia su régimen municipal. En la v2.1 reemplazan al recurso `/municipios` de la v1.0.

La fuente que informa la API para estos datos es "DPE - INDEC". Los IDs tienen 6 dígitos: los dos primeros son los de la provincia.

Recurso: [`/gobiernos-locales`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales). Todos sus parámetros están en la [referencia de la API](/georef-ar-api/referencia/).

## Categorías

Con el parámetro `categoria` filtrás por tipo de gobierno local. Estas son las categorías y la cantidad de gobiernos locales de cada una, según el campo `total` de la API al 25/09/2026:

| `categoria` | Total |
| --- | --- |
| Municipio | 1210 |
| Comuna | 563 |
| Comisión Municipal | 215 |
| Comuna Rural | 113 |
| Comisión de Fomento | 96 |
| Junta de Gobierno | 83 |

En total hay 2280 gobiernos locales.

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?categoria=Junta de Gobierno&max=1&campos=id,nombre,categoria`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?categoria=Junta%20de%20Gobierno&max=1&campos=id,nombre,categoria)

```json
{
    "cantidad": 1,
    "gobiernos_locales": [
        {
            "categoria": "Junta de Gobierno",
            "id": "309205",
            "nombre": "El Gramiyal"
        }
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 83
}
```

## Campos

Con `campos=completo` obtenés todos los campos:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?id=220161&campos=completo`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?id=220161&campos=completo)

```json
{
    "cantidad": 1,
    "gobiernos_locales": [
        {
            "categoria": "Municipio",
            "centroide": {
                "lat": -27.112132893,
                "lon": -59.231495362
            },
            "fuente": "DPE - INDEC",
            "id": "220161",
            "nombre": "Makallé",
            "nombre_completo": "Municipio Makallé",
            "provincia": {
                "id": "22",
                "interseccion": 0.0,
                "nombre": "Chaco"
            }
        }
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 1
}
```

## Dónde aparece `gobierno_local`

- Como **campo de respuesta** en `/ubicacion` (con `division=politica`), `/localidades`, `/localidades-censales` y `/asentamientos`.
- Como **parámetro de filtro** `gobierno_local` en `/localidades`, `/localidades-censales` y `/asentamientos`.
- Como tipo de entidad en `interseccion=gobierno_local:<id>` para `/provincias`, `/departamentos`, `/aglomerados` y `/calles` (ver [Operaciones con geometrías](/georef-ar-api/geom-operations/)).

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/localidades?gobierno_local=100077&campos=id,nombre`](https://apis.datos.gob.ar/georef/api/v2.1/localidades?gobierno_local=100077&campos=id,nombre)

```json
{
    "cantidad": 3,
    "inicio": 0,
    "localidades": [
        { "id": "10035060", "nombre": "Farallón Negro" },
        { "id": "10035070", "nombre": "Hualfín" },
        { "id": "10035120", "nombre": "Los Nacimientos" }
    ],
    "parametros": { ... },
    "total": 3
}
```

## ¿Y `/municipios`?

`/municipios` sigue respondiendo en la v2.1, pero está **deprecado**: filtra implícitamente por `categoria=Municipio` y agrega los encabezados `deprecation: true` y `link: </api/v2.1/gobiernos-locales>; rel="successor-version"`. Para la misma consulta, `/gobiernos-locales?categoria=Municipio` devuelve los mismos resultados. Ver [Migrar desde v1.0](/georef-ar-api/migrar-desde-v1/).
