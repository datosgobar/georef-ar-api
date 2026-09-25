---
title: "Ejemplos de uso"
---

Estos son algunos ejemplos rápidos con los recursos `GET` de la v2.1. Todas las respuestas son reales (recortadas con `{ ... }`). Para ver todos los parámetros de cada recurso, andá a la [referencia de la API](/georef-ar-api/referencia/).

:::note
Usá siempre la URL con versión: `https://apis.datos.gob.ar/georef/api/v2.1/`. La URL sin versión responde con la v1.0.
:::

### Búsqueda de provincias

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=cordoba`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=cordoba)

```json
{
    "cantidad": 1,
    "inicio": 0,
    "parametros": { ... },
    "provincias": [
        {
            "centroide": {
                "lat": -32.144799387,
                "lon": -63.801973467
            },
            "id": "14",
            "nombre": "Córdoba"
        }
    ],
    "total": 1
}
```

### Búsqueda de departamentos

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/departamentos?provincia=jujuy&max=16`](https://apis.datos.gob.ar/georef/api/v2.1/departamentos?provincia=jujuy&max=16)

```json
{
    "cantidad": 16,
    "departamentos": [
        {
            "centroide": {
                "lat": -24.447537267,
                "lon": -65.101285905
            },
            "id": "38014",
            "nombre": "El Carmen",
            "provincia": {
                "id": "38",
                "nombre": "Jujuy"
            }
        },
        { ... } // 15 departamentos omitidos
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 16
}
```

### Búsqueda de gobiernos locales

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?provincia=tucuman&aplanar`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?provincia=tucuman&aplanar)

```json
{
    "cantidad": 10,
    "gobiernos_locales": [
        {
            "centroide_lat": -27.056420716,
            "centroide_lon": -65.302491897,
            "id": "900070",
            "nombre": "Bella Vista",
            "provincia_id": "90",
            "provincia_nombre": "Tucumán"
        },
        { ... } // 9 gobiernos locales omitidos
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 112
}
```

Más detalles en [Gobiernos locales](/georef-ar-api/gobiernos-locales/).

### Búsqueda de localidades

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/localidades?provincia=chubut&campos=nombre`](https://apis.datos.gob.ar/georef/api/v2.1/localidades?provincia=chubut&campos=nombre)

```json
{
    "cantidad": 10,
    "inicio": 0,
    "localidades": [
        {
            "id": "26021040",
            "nombre": "Diadema Argentina"
        },
        { ... } // 9 resultados omitidos
    ],
    "parametros": {
        "campos": ["id", "nombre"],
        "categoria": "Localidad simple,Componente de localidad compuesta,entidad",
        "provincia": "chubut"
    },
    "total": 91
}
```

Fijate que `parametros` muestra un filtro `categoria` que no pediste: `/localidades` lo aplica siempre (ver [Localidades y asentamientos](/georef-ar-api/localities/)).

### Normalización de direcciones

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/direcciones?departamento=merlo&direccion=Florida al 2950`](https://apis.datos.gob.ar/georef/api/v2.1/direcciones?departamento=merlo&direccion=Florida%20al%202950)

```json
{
    "cantidad": 1,
    "direcciones": [
        {
            "altura": {
                "unidad": null,
                "valor": 2950
            },
            "calle": {
                "categoria": "CALLE",
                "id": "065390100003490",
                "nombre": "FLORIDA"
            },
            "calle_cruce_1": {
                "categoria": null,
                "id": null,
                "nombre": null
            },
            "calle_cruce_2": {
                "categoria": null,
                "id": null,
                "nombre": null
            },
            "departamento": {
                "id": "06539",
                "nombre": "Merlo"
            },
            "localidad": {
                "id": null,
                "nombre": null
            },
            "localidad_censal": {
                "id": "06539010",
                "nombre": "Merlo"
            },
            "nomenclatura": "FLORIDA 2950, Merlo, Merlo, Buenos Aires",
            "piso": null,
            "provincia": {
                "id": "06",
                "nombre": "Buenos Aires"
            },
            "ubicacion": {
                "lat": -34.71409157867347,
                "lon": -58.734699966
            }
        }
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 4
}
```

### Listado de calles

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/calles?departamento=rio chico&categoria=avenida`](https://apis.datos.gob.ar/georef/api/v2.1/calles?departamento=rio%20chico&categoria=avenida)

```json
{
    "calles": [
        {
            "altura": {
                "fin": { "derecha": 0, "izquierda": 0 },
                "inicio": { "derecha": 0, "izquierda": 0 }
            },
            "categoria": "AV",
            "departamento": {
                "id": "78049",
                "nombre": "Río Chico"
            },
            "id": "780490200000025",
            "localidad": {
                "id": null,
                "nombre": null
            },
            "localidad_censal": {
                "id": "78049020",
                "nombre": "Gobernador Gregores"
            },
            "nombre": "AV CANADON LEON",
            "nomenclatura": "AV CANADON LEON, Gobernador Gregores, Río Chico, Santa Cruz",
            "provincia": {
                "id": "78",
                "nombre": "Santa Cruz"
            }
        },
        { ... } // 9 resultados omitidos
    ],
    "cantidad": 10,
    "inicio": 0,
    "parametros": { ... },
    "total": 10
}
```

### Unidades que contienen un punto

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-34.6037389&lon=-58.3815704&division=geoestadistica`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-34.6037389&lon=-58.3815704&division=geoestadistica)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "aglomerado": {
            "id": "0001",
            "nombre": "Gran Buenos Aires"
        },
        "departamento": {
            "id": "02007",
            "nombre": "Comuna 1"
        },
        "fraccion_censal": {
            "id": "0200709"
        },
        "lat": -34.6037389,
        "localidad_censal": {
            "id": "02007010",
            "nombre": "CABA - Comuna 1"
        },
        "lon": -58.3815704,
        "provincia": {
            "id": "02",
            "nombre": "Ciudad Autónoma de Buenos Aires"
        },
        "radio_censal": {
            "id": "020070903"
        }
    }
}
```

Más ejemplos de `/ubicacion` en [Operaciones con geometrías](/georef-ar-api/geom-operations/).

## Formatos de respuesta

Con el parámetro `formato` elegís cómo querés la respuesta. Los recursos de listado aceptan `json` (por defecto), `csv`, `geojson`, `xml`, `shp` y `gpkg`, con estas excepciones: `/calles` y `/cuadras` no aceptan `geojson`, y `/ubicacion` solo acepta `json`, `geojson` y `xml`. Si pedís un formato no admitido, la respuesta es un error 400 que lista los valores válidos bajo la clave `ayuda`:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/calles?max=1&formato=geojson`](https://apis.datos.gob.ar/georef/api/v2.1/calles?max=1&formato=geojson)

```json
{
    "errores": [
        {
            "ayuda": ["csv", "gpkg", "json", "shp", "xml"],
            "codigo_interno": 1002,
            "mensaje": "El parámetro debe tomar el valor de uno de los listados bajo la clave 'ayuda'.",
            "nombre_parametro": "formato",
            "ubicacion": "querystring"
        }
    ]
}
```

## Paginación

`max` acepta hasta 5000 resultados por consulta, y la suma de `max` + `inicio` no puede superar 10000. Si te pasás, la API devuelve un error 400 (`codigo_interno` 1001 o 1009).
