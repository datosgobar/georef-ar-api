---
title: "Modelo de datos para Georef"
---

**Versión de datos**: 13.0.0 (archivos del 9 y 10 de abril de 2026, según sus metadatos)

El ETL de Georef produce los archivos con los datos de las entidades geográficas. Algunos se indexan en la API y otros sirven para que descargues la base completa en distintos formatos.

Los archivos que indexa la API tienen formato [NDJSON](https://github.com/ndjson/ndjson-spec): un archivo de texto donde cada línea (separada por `\n`) es un objeto JSON válido. Son:

- `provincias.ndjson`
- `departamentos.ndjson`
- `aglomerados.ndjson`
- `fracciones_censales.ndjson`
- `radios_censales.ndjson`
- `gobiernos_locales.ndjson`
- `localidades_censales.ndjson`
- `asentamientos.ndjson`
- `localidades.ndjson`
- `calles.ndjson`
- `intersecciones.ndjson`
- `cuadras.ndjson`
- `establecimientos_educativos.ndjson`
- `instituciones_universitarias.ndjson`

Para descargas también se generan versiones JSON, CSV y GeoJSON de cada archivo (ver [Descarga de base completa](/georef-ar-api/download/)). **Si vas a procesar todos los datos, usá NDJSON**: se puede leer por partes (línea a línea), lo que simplifica trabajar con archivos grandes.

:::caution[A validar]
Los ejemplos de esta página son la primera entidad real de cada archivo NDJSON publicado por la descarga de la v2.1 (versión de datos 13.0.0, consultados el 25/09/2026), con la geometría recortada. La estructura surge de esos ejemplos; no pudimos contrastarla con una especificación del ETL, así que un campo opcional que no aparezca en el primer registro puede faltar acá.
:::

## Fuentes

Cada entidad trae un campo `fuente`. En los archivos de la versión 13.0.0 aparecen, entre otros:

- **IGN** (Instituto Geográfico Nacional): provincias y departamentos.
- **INDEC**: aglomerados, fracciones y radios censales, localidades censales, localidades, calles, intersecciones y cuadras. Ver [códigos geográficos del INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-Codgeo).
- **DPE - INDEC**: gobiernos locales.
- **BAHRA** ([Base de Asentamientos Humanos de la República Argentina](http://www.bahra.gob.ar/)): base de asentamientos y localidades; el campo `fuente` de cada registro indica el origen puntual (por ejemplo, "INDEC. ACA").
- **Mapa Educativo Nacional - DIEE**: establecimientos educativos.

## Archivos

La primera línea de cada archivo tiene los metadatos. Por ejemplo, la de `provincias.ndjson`:

```json
{"fecha_creacion":"2026-04-09 23:30:03.319204+00:00","timestamp":1775777403,"version":"13.0.0","cantidad":24}
```

- `fecha_creacion`: fecha de creación.
- `timestamp`: *timestamp* de creación.
- `version`: versión de los datos.
- `cantidad`: cantidad de entidades del archivo.

El resto de las líneas tiene una entidad cada una. Todas las geometrías están en formato GeoJSON y usan el sistema de coordenadas **WGS84** (**EPSG 4326**). En los ejemplos, las líneas se muestran con sangría y la geometría recortada (`"coordinates": "…"`); en el archivo cada entidad ocupa una sola línea.

### Provincias (`provincias.ndjson`)

Entidades en la versión 13.0.0: 24.

```json
{
    "id": "02",
    "nombre": "Ciudad Autónoma de Buenos Aires",
    "nombre_completo": "Ciudad Autónoma de Buenos Aires",
    "fuente": "IGN",
    "categoria": "Ciudad Autónoma",
    "centroide": {
        "lon": -58.445876325,
        "lat": -34.614442065
    },
    "iso_id": "AR-C",
    "iso_nombre": "Ciudad Autónoma de Buenos Aires",
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Departamentos (`departamentos.ndjson`)

Entidades en la versión 13.0.0: 529.

```json
{
    "id": "30015",
    "nombre": "Concordia",
    "nombre_completo": "Departamento Concordia",
    "provincia": {
        "id": "30",
        "nombre": "Entre Ríos",
        "interseccion": 0.0
    },
    "fuente": "IGN",
    "categoria": "Departamento",
    "centroide": {
        "lon": -58.23786969,
        "lat": -31.290298372
    },
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Aglomerados (`aglomerados.ndjson`)

Entidades en la versión 13.0.0: 119.

```json
{
    "id": "1113",
    "nombre": "Domselaar - Barrio Parque Las Acacias",
    "fuente": "INDEC",
    "centroide": {
        "lon": -58.285127423,
        "lat": -35.071025356
    },
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Fracciones censales (`fracciones_censales.ndjson`)

Entidades en la versión 13.0.0: 6.571.

```json
{
    "id": "0667910",
    "fuente": "INDEC",
    "provincia": {
        "id": "06",
        "nombre": "Buenos Aires",
        "interseccion": 0.0
    },
    "departamento": {
        "id": "06679",
        "nombre": "Rivadavia"
    },
    "centroide": {
        "lon": -63.038968583,
        "lat": -35.568259353
    },
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Radios censales (`radios_censales.ndjson`)

Entidades en la versión 13.0.0: 66.515.

```json
{
    "id": "221402203",
    "fuente": "INDEC",
    "provincia": {
        "id": "22",
        "nombre": "Chaco"
    },
    "departamento": {
        "id": "22140",
        "nombre": "San Fernando"
    },
    "fraccion_censal": {
        "id": "2214022",
        "interseccion": 0.0
    },
    "centroide": {
        "lon": -58.962357395,
        "lat": -27.65121747
    },
    "categoria": "Mixto",
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Gobiernos locales (`gobiernos_locales.ndjson`)

Entidades en la versión 13.0.0: 2.280.

```json
{
    "id": "540504",
    "nombre": "San Pedro",
    "nombre_completo": "Municipio San Pedro",
    "provincia": {
        "id": "54",
        "nombre": "Misiones",
        "interseccion": 0.0
    },
    "fuente": "DPE - INDEC",
    "categoria": "Municipio",
    "centroide": {
        "lon": -53.943330341,
        "lat": -26.710300045
    },
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Localidades censales (`localidades_censales.ndjson`)

Entidades en la versión 13.0.0: 4.023.

```json
{
    "id": "06280040",
    "nombre": "Miramar",
    "fuente": "INDEC",
    "provincia": {
        "id": "06",
        "nombre": "Buenos Aires"
    },
    "departamento": {
        "id": "06280",
        "nombre": "General Alvarado"
    },
    "gobierno_local": {
        "id": null,
        "nombre": null
    },
    "categoria": "Componente de localidad compuesta",
    "funcion": null,
    "centroide": {
        "lon": -57.830489221,
        "lat": -38.252704473
    },
    "geometria": {
        "type": "MultiPolygon",
        "coordinates": "…"
    }
}
```

### Asentamientos (`asentamientos.ndjson`)

Entidades en la versión 13.0.0: 14.466.

```json
{
    "id": "14098A77",
    "nombre": "Tres Pozos",
    "fuente": "INDEC. ACA",
    "provincia": {
        "id": "14",
        "nombre": "Córdoba"
    },
    "departamento": {
        "id": "14098",
        "nombre": "Río Cuarto"
    },
    "gobierno_local": {
        "id": null,
        "nombre": null
    },
    "localidad_censal": {
        "id": null,
        "nombre": null
    },
    "categoria": "Paraje",
    "centroide": {
        "lon": -64.105625052,
        "lat": -32.407731637
    },
    "geometria": {
        "type": "MultiPoint",
        "coordinates": "…"
    }
}
```

### Localidades (`localidades.ndjson`)

Entidades en la versión 13.0.0: 4.028.

```json
{
    "id": "30008050",
    "nombre": "Hocker",
    "fuente": "INDEC",
    "provincia": {
        "id": "30",
        "nombre": "Entre Ríos"
    },
    "departamento": {
        "id": "30008",
        "nombre": "Colón"
    },
    "gobierno_local": {
        "id": "309015",
        "nombre": "Colonia Hocker"
    },
    "localidad_censal": {
        "id": "30008050",
        "nombre": "Hocker"
    },
    "categoria": "Localidad simple",
    "centroide": {
        "lon": -58.339488507,
        "lat": -32.088313118
    },
    "geometria": {
        "type": "Point",
        "coordinates": "…"
    }
}
```

### Calles (`calles.ndjson`)

Entidades en la versión 13.0.0: 333.800.

```json
{
    "id": "062520100103600",
    "nombre": "CALLE SN",
    "fuente": "INDEC",
    "provincia": {
        "id": "06",
        "nombre": "Buenos Aires"
    },
    "departamento": {
        "id": "06252",
        "nombre": "Escobar"
    },
    "localidad_censal": {
        "id": "06252010",
        "nombre": "Escobar"
    },
    "localidad": {
        "id": "0625201001",
        "nombre": "Belén de Escobar"
    },
    "categoria": "CALLE",
    "altura": {
        "inicio": {
            "derecha": 0,
            "izquierda": 0
        },
        "fin": {
            "derecha": 0,
            "izquierda": 0
        }
    },
    "geometria": {
        "type": "MultiLineString",
        "coordinates": "…"
    }
}
```

### Intersecciones de calles (`intersecciones.ndjson`)

El ID de cada intersección tiene tres partes: el ID de la primera calle. el ID de la segunda y el número de intersección entre ambas (desde `01`).

Entidades en la versión 13.0.0: 1.166.180.

```json
{
    "id": "020070100106130-020280100006130-01",
    "calle_a": {
        "id": "020070100106130",
        "nombre": "GUANAHANI",
        "fuente": "INDEC",
        "provincia": {
            "id": "02",
            "nombre": "Ciudad Autónoma de Buenos Aires"
        },
        "departamento": {
            "id": "02007",
            "nombre": "Comuna 1"
        },
        "localidad_censal": {
            "id": "02007010",
            "nombre": "CABA - Comuna 1"
        },
        "localidad": {
            "id": "0200701001",
            "nombre": "Constitución"
        },
        "categoria": "CALLE"
    },
    "calle_b": {
        "id": "020280100006130",
        "nombre": "GUANAHANI",
        "fuente": "INDEC",
        "provincia": {
            "id": "02",
            "nombre": "Ciudad Autónoma de Buenos Aires"
        },
        "departamento": {
            "id": "02028",
            "nombre": "Comuna 4"
        },
        "localidad_censal": {
            "id": "02028010",
            "nombre": "CABA - Comuna 4"
        },
        "localidad": {
            "id": null,
            "nombre": null
        },
        "categoria": "CALLE"
    },
    "geometria": {
        "type": "Point",
        "coordinates": "…"
    }
}
```

### Cuadras (`cuadras.ndjson`)

El ID de la cuadra tiene 22 dígitos: los primeros 15 son el ID de la calle.

Entidades en la versión 13.0.0: 2.076.269.

```json
{
    "id": "0664401000007902895356",
    "calle": {
        "id": "066440100000790",
        "nombre": "CALLE SN",
        "fuente": "INDEC",
        "provincia": {
            "id": "06",
            "nombre": "Buenos Aires"
        },
        "departamento": {
            "id": "06644",
            "nombre": "Pinamar"
        },
        "localidad_censal": {
            "id": "06644010",
            "nombre": "Pinamar"
        },
        "localidad": {
            "id": null,
            "nombre": null
        },
        "categoria": "CALLE"
    },
    "altura": {
        "inicio": {
            "derecha": 0,
            "izquierda": 0
        },
        "fin": {
            "derecha": 0,
            "izquierda": 0
        }
    },
    "geometria": {
        "type": "MultiLineString",
        "coordinates": "…"
    }
}
```

### Establecimientos educativos (`establecimientos_educativos.ndjson`)

Entidades en la versión 13.0.0: 62.271.

```json
{
    "id": "062068500",
    "nombre": "HUMANOS",
    "fuente": "Mapa Educativo Nacional - DIEE",
    "categoria": "",
    "domicilio": "CHAMPAGNAT 4579",
    "localidad": "CANNING",
    "gestion": "Privado",
    "niveles": "Común-Primaria 6años;",
    "centroide": {
        "lon": -58.509377125,
        "lat": -34.888583139
    },
    "geometria": {
        "type": "MultiPoint",
        "coordinates": "…"
    },
    "provincia": {
        "id": "06",
        "nombre": "Buenos Aires"
    },
    "departamento": {
        "id": "06270",
        "nombre": "Ezeiza"
    }
}
```

### Instituciones universitarias (`instituciones_universitarias.ndjson`)

Entidades en la versión 13.0.0: 1.441.

```json
{
    "id": "70600928",
    "nombre": "Centro Universitario Regional Lobos - Universidad de Buenos Aires",
    "fuente": "",
    "categoria": "",
    "domicilio": "Buenos Aires 541",
    "localidad": "Lobos",
    "gestion": "Estatal",
    "niveles": "Pregrado - Grado",
    "universidad": "Universidad de Buenos Aires",
    "unidad_academica": "Centro Universitario Regional Lobos",
    "centroide": {
        "lon": -59.0973812,
        "lat": -35.1809247
    },
    "geometria": {
        "type": "MultiPoint",
        "coordinates": "…"
    },
    "provincia": {
        "id": "06",
        "nombre": "Buenos Aires"
    },
    "departamento": {
        "id": "06483",
        "nombre": "Lobos"
    }
}
```

## Procesamiento

Para procesar los archivos con Python alcanza con el módulo estándar `json`. Iterá sobre el archivo abierto para no cargarlo entero en memoria:

```python
import json

with open('calles.ndjson', encoding='utf-8') as f:
    # línea de metadatos
    metadata = json.loads(next(f))

    # una entidad por línea
    for line in f:
        street = json.loads(line)
        # street es un dict con los datos de la calle
```
