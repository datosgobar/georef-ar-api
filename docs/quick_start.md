# Ejemplos de uso

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
 

- [Ejemplos rápidos](#ejemplos-rapidos)
    - [Búsqueda de provincias](#busqueda-de-provincias)
    - [Búsqueda de departamentos](#busqueda-de-departamentos)
    - [Búsqueda de municipios](#busqueda-de-municipios)
    - [Búsqueda de localidades](#busqueda-de-localidades)
    - [Normalización de direcciones](#normalizacion-de-direcciones)
    - [Entidades geográficas en un punto](#entidades-geograficas-en-un-punto)
- [Ejemplos de operaciones por lotes](#ejemplos-de-operaciones-por-lotes)
    - [Búsqueda de municipios en lotes](#busqueda-de-municipios-en-lotes)
    - [Normalización de direcciones en lotes](#normalizacion-de-direcciones-en-lotes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Ejemplos rápidos
A continuación, se muestran algunos ejemplos de uso de la API, utilizando los recursos `GET`:

### Búsqueda de provincias
`GET` [`https://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba`](https://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba)
```
{
    "provincias": [
        {
            "fuente": "IGN",
            "id": "14",
            "centroide": {
                "lat": -32.142933,
                "lon": -63.801753
            },
            "nombre": "CÓRDOBA"
        }
    ],
    "cantidad": 1,
    "total": 1,
    "inicio": 0
}
```

### Búsqueda de departamentos
`GET` [`https://apis.datos.gob.ar/georef/api/departamentos?provincia=jujuy&max=16`](https://apis.datos.gob.ar/georef/api/departamentos?provincia=jujuy&max=16)
```
{
    "departamentos": [
        {
            "fuente": "IGN",
            "id": "38042",
            "centroide": {
                "lat": -24.194923,
                "lon": -65.12645
            },
            "nombre": "PALPALÁ",
            "provincia": {
                "id": "38",
                "nombre": "JUJUY"
            }
        },
        { ... } // 15 departamentos omitidos
    ],
    "cantidad": 16,
    "total": 16,
    "inicio": 0
}
```

### Búsqueda de municipios
`GET` [`https://apis.datos.gob.ar/georef/api/municipios?departamento=graneros`](https://apis.datos.gob.ar/georef/api/municipios?departamento=graneros)
```
{
    "municipios": [
        {
            "centroide": {
                "lat": -27.816619,
                "lon": -65.199594
            },
            "departamento": {
                "id": "90035",
                "nombre": "Graneros"
            },
            "fuente": "IGN",
            "id": "908210",
            "nombre": "Taco Ralo",
            "provincia": {
                "id": "90",
                "nombre": "Tucumán"
            }
        },
        { ... } // 2 municipios omitidos
    ],
    "cantidad": 3,
    "total": 3,
    "inicio": 0
}
```

### Búsqueda de localidades
`GET` [`https://apis.datos.gob.ar/georef/api/localidades?provincia=chubut&campos=nombre`](https://apis.datos.gob.ar/georef/api/localidades?provincia=chubut&campos=nombre)
```
{
    "localidades": [
        {
            "fuente": "BAHRA",
            "id": "26007030000",
            "nombre": "PUERTO PIRAMIDE"
        },
        { ... } // 9 resultados omitidos
    ],
    "cantidad": 10,
    "total": 90,
    "inicio": 0
}
```

### Normalización de direcciones
`GET` [`https://apis.datos.gob.ar/georef/api/direcciones?provincia=bsas&direccion=Florida 1801`](https://apis.datos.gob.ar/georef/api/direcciones?provincia=bsas&direccion=Florida%201801)
```
{
    "direcciones": [
        {
            "altura": 1801,
            "departamento": {
                "id": "06270",
                "nombre": "JOSÉ M. EZEIZA"
            },
            "fuente": "INDEC",
            "id": "0627001001875",
            "nombre": "FLORIDA",
            "nomenclatura": "FLORIDA 1801, JOSÉ M. EZEIZA, BUENOS AIRES",
            "provincia": {
                "id": "06",
                "nombre": "BUENOS AIRES"
            },
            "tipo": "CALLE"
        },
        { ... } // 9 resultados omitidos
    ],
    "cantidad": 1,
    "total": 13,
    "inicio": 0
}
```

### Entidades geográficas en un punto
`GET` [`https://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529)
```
{
    "ubicacion": {
        "departamento": {
            "id": "10035",
            "nombre": "BELÉN"
        },
        "fuente": "IGN",
        "lat": -27.2741,
        "lon": -66.7529,
        "municipio": {
            "id": "100077",
            "nombre": "HUALFÍN"
        },
        "provincia": {
            "id": "10",
            "nombre": "CATAMARCA"
        }
    }
}
```

## Ejemplos de operaciones por lotes
Todos los recursos de la API tienen una variante `POST`, que permite realizar varias consultas en una misma petición. De esta forma, se pueden envíar más consultas en menos tiempo.

### Búsqueda de municipios en lotes
`POST` `https://apis.datos.gob.ar/georef/api/municipios`
```json
{
    "municipios": [
        {
            "nombre": "belgrano",
            "max": 1,
            "campos": "id, nombre"
        },
        {
            "nombre": "martin",
            "max": 1,
            "provincia": "la pampa",
			"aplanar": true
        }
    ]
}
```
Resultados:
```json
{
    "resultados": [
        {
            "municipios": [
                {
                    "fuente": "IGN",
                    "id": "060301",
                    "nombre": "General Belgrano"
                }
            ],
            "cantidad": 1,
            "total": 8,
            "inicio": 0
        },
        {
            "municipios": [
                {
                    "centroide_lat": -35.361211,
                    "centroide_lon": -64.294073,
                    "departamento_id": "42133",
                    "departamento_nombre": "Realicó",
                    "fuente": "IGN",
                    "id": "420126",
                    "nombre": "Embajador Martini",
                    "provincia_id": "42",
                    "provincia_nombre": "La Pampa"
                }
            ],
            "cantidad": 1,
            "total": 2,
            "inicio": 0
        }
    ]
}
```

### Normalización de direcciones en lotes
`POST` `https://apis.datos.gob.ar/georef/api/direcciones`
```json
{
    "direcciones": [
        {
            "direccion": "santa fe 3100",
            "max": 1,
            "campos": "id, nombre, altura"
        },
        {
            "direccion": "corientes 4010",
            "max": 1,
			"campos": "id, nombre, altura",
			"departamento": "General López"
        }
    ]
}
```
Resultados:
```json
{
    "resultados": [
        {
            "direcciones": [
                {
                    "altura": 3100,
                    "fuente": "INDEC",
                    "id": "0642701011435",
                    "nombre": "SANTA FE"
                }
            ],
            "cantidad": 1,
            "total": 25,
            "inicio": 0
        },
        {
            "direcciones": [
                {
                    "altura": 4010,
                    "fuente": "INDEC",
                    "id": "8204229000610",
                    "nombre": "CORRIENTES"
                }
            ],
            "cantidad": 1,
            "total": 1,
            "inicio": 0
        }
    ]
}
```
