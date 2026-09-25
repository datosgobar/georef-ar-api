---
title: "Operaciones con geometrías"
---

La API te deja operar con las geometrías de las entidades geográficas. Estos son los recursos y parámetros que lo permiten.

## Parámetro `interseccion`

Con `interseccion` filtrás entidades según se crucen o no con las geometrías de otras. El valor tiene este formato:

```
interseccion=<tipo de entidad>:<id 1>[:<id 2>:...][, <tipo de entidad>:<id>...]
```

La API busca entidades que compartan área con **cualquiera** de las entidades listadas. Estos son los recursos que aceptan el parámetro y los tipos de entidad que podés usar en cada uno:

| Recurso | Tipos de entidad en `interseccion` |
| --- | --- |
| `/provincias` | `departamento`, `gobierno_local`, `calle` |
| `/departamentos` | `provincia`, `gobierno_local`, `calle` |
| `/gobiernos-locales` | `provincia`, `departamento`, `calle` |
| `/fracciones-censales`, `/radios-censales` | `provincia`, `departamento`, `calle` |
| `/aglomerados` | `provincia`, `departamento`, `gobierno_local`, `calle` |
| `/calles` | `provincia`, `departamento`, `gobierno_local`, `calle` |

:::caution[A validar]
El código de la v2.1 acepta `interseccion` en `/aglomerados`, pero en las pruebas del 25/09/2026 devolvió 0 resultados incluso para casos que deberían coincidir (por ejemplo, `aglomerados?interseccion=departamento:82084`, el departamento Rosario, no devuelve "Gran Rosario").
:::

:::caution[Cambio respecto de v1.0]
En la v1.0 el tipo de entidad era `municipio`. En la v2.1 se llama `gobierno_local`: `interseccion=municipio:...` devuelve un error 400.
:::

Algunos ejemplos:

- `/gobiernos-locales?interseccion=departamento:18105`: gobiernos locales que se cruzan con el departamento 18105.
- `/departamentos?interseccion=gobierno_local:620133:540378`: departamentos que se cruzan con el gobierno local 620133 **o** con el 540378.
- `/calles?interseccion=gobierno_local:141372`: calles del gobierno local 141372.
- `/gobiernos-locales?interseccion=calle:141470100000265`: gobierno local que contiene la calle 141470100000265.

:::caution[IDs inválidos]
Los IDs que no correspondan a una entidad existente se ignoran.
:::

Ejemplo completo:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?interseccion=departamento:18105`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?interseccion=departamento:18105)

```json
{
    "cantidad": 10,
    "gobiernos_locales": [
        {
            "centroide": {
                "lat": -29.061289968,
                "lon": -58.403975796
            },
            "id": "180231",
            "nombre": "Felipe Yofre",
            "provincia": {
                "id": "18",
                "nombre": "Corrientes"
            }
        },
        { ... } // 9 resultados omitidos
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 13
}
```

Aunque `/provincias` acepta `interseccion`, para buscar provincias conviene filtrar por ID, que es más rápido. Por ejemplo, `/provincias?interseccion=departamento:18105` equivale a `/provincias?id=18`, porque los dos primeros dígitos del ID de un departamento son siempre los de su provincia.

## Recurso `/ubicacion`

`/ubicacion` usa las geometrías para determinar qué entidades contienen el punto que indicás con `lat` y `lon`. Con el parámetro `division` elegís qué tipo de división querés:

- `division=politica` (por defecto): provincia, departamento y gobierno local.
- `division=geoestadistica`: provincia, departamento, aglomerado, localidad censal, fracción censal y radio censal.

Con `campos=completo` también obtenés la fuente de cada entidad, la calle más cercana y una `nomenclatura`.

Según el punto, puede que alguna entidad no exista (por ejemplo, un punto fuera de todo gobierno local): en ese caso sus campos vuelven en `null`.

Con gobierno local:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "departamento": {
            "id": "10035",
            "nombre": "Belén"
        },
        "gobierno_local": {
            "id": "100077",
            "nombre": "Hualfín"
        },
        "lat": -27.2741,
        "lon": -66.7529,
        "provincia": {
            "id": "10",
            "nombre": "Catamarca"
        }
    }
}
```

Sin gobierno local:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-28.504&lon=-62.898`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-28.504&lon=-62.898)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "departamento": {
            "id": "86028",
            "nombre": "Avellaneda"
        },
        "gobierno_local": {
            "id": null,
            "nombre": null
        },
        "lat": -28.504,
        "lon": -62.898,
        "provincia": {
            "id": "86",
            "nombre": "Santiago del Estero"
        }
    }
}
```

División geoestadística del mismo primer punto:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529&division=geoestadistica`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529&division=geoestadistica)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "aglomerado": { "id": null, "nombre": null },
        "departamento": { "id": "10035", "nombre": "Belén" },
        "fraccion_censal": { "id": "1003501" },
        "lat": -27.2741,
        "localidad_censal": { "id": null, "nombre": null },
        "lon": -66.7529,
        "provincia": { "id": "10", "nombre": "Catamarca" },
        "radio_censal": { "id": "100350101" }
    }
}
```

## Recurso `/establecimientos-cercanos`

Devuelve los establecimientos educativos y universitarios que están a menos de `distancia` metros (por defecto 1000, entre 10 y 500000) de un punto, ordenados por distancia. Ver [Entidades censales y establecimientos](/georef-ar-api/entidades-censales-y-establecimientos/#establecimientos).
