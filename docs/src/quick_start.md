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
`GET` [`https://apis.datos.gob.ar/georef/api/municipios?provincia=tucuman&aplanar`](https://apis.datos.gob.ar/georef/api/municipios?provincia=tucuman&aplanar)
```
{
    "municipios": [
        {
            "centroide_lat": -27.816619,
            "centroide_lon": -65.199594,
            "id": "908210",
            "nombre": "Taco Ralo",
            "provincia_id": "90",
            "provincia_nombre": "Tucumán"
        },
        { ... } // 9 municipios omitidos
    ],
    "cantidad": 10,
    "total": 112,
    "inicio": 0
}
```

### Búsqueda de localidades
`GET` [`https://apis.datos.gob.ar/georef/api/localidades?provincia=chubut&campos=nombre`](https://apis.datos.gob.ar/georef/api/localidades?provincia=chubut&campos=nombre)
```
{
    "localidades": [
        {
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

### Listado de calles
`GET` [`https://apis.datos.gob.ar/georef/api/calles?departamento=rio chico&tipo=avenida`](https://apis.datos.gob.ar/georef/api/calles?departamento=rio chico&tipo=avenida)
```
{
    "calles": [
        {
            "altura": {
                "fin": {
                    "derecha": 0,
                    "izquierda": 0
                },
                "inicio": {
                    "derecha": 0,
                    "izquierda": 0
                }
            },
            "departamento": {
                "id": "90077",
                "nombre": "Río Chico"
            },
            "id": "9007701000050",
            "nombre": "AV GRL SAVIO",
            "nomenclatura": "AV GRL SAVIO, Río Chico, Tucumán",
            "provincia": {
                "id": "90",
                "nombre": "Tucumán"
            },
            "tipo": "AV"
        }, { ... } // 2 resultados omitidos
    ],
    "cantidad": 3,
    "total": 3,
    "inicio": 0
}
```

## Ejemplos de operaciones por lotes
Todos los recursos de la API tienen una variante `POST`, que permite realizar varias consultas en una misma petición. De esta forma, se pueden envíar más consultas en menos tiempo.

A diferencia de los recursos `GET`, los ejemplos de operaciones por lotes se muestran utilizando comandos construídos sobre `curl`.

### Búsqueda de municipios en lotes
```
curl -X POST "https://apis.datos.gob.ar/georef/api/municipios" \
-H 'Content-Type: application/json' -d'
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
'
```
Resultados:
```json
{
    "resultados": [
        {
            "municipios": [
                {
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
```
curl -X POST "https://apis.datos.gob.ar/georef/api/direcciones" \
-H 'Content-Type: application/json' -d'
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
'
```
Resultados:
```json
{
    "resultados": [
        {
            "direcciones": [
                {
                    "altura": 3100,
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

### Entidades geográficas en varios puntos
```
curl -X POST "https://apis.datos.gob.ar/georef/api/ubicacion" \
-H 'Content-Type: application/json' -d'
{
    "ubicaciones": [
        {
            "lat": -27.274161,
            "lon": -66.752929,
            "campos": "completo"
        },
        {
            "lat": -31.480693,
            "lon": -59.092813,
            "aplanar": true,
            "campos": "completo"
        }
    ]
}
'
```
Resultados:
```json
{
    "resultados": [
        {
            "ubicacion": {
                "fuente": "IGN",
                "municipio": {
                    "nombre": "Hualfín",
                    "id": "100077"
                },
                "lon": -66.752929,
                "provincia": {
                    "nombre": "Catamarca",
                    "id": "10"
                },
                "lat": -27.274161,
                "departamento": {
                    "nombre": "Belén",
                    "id": "10035"
                }
            }
        },
        {
            "ubicacion": {
                "departamento_nombre": "Villaguay",
                "lon": -59.092813,
                "municipio_id": null,
                "lat": -31.480693,
                "fuente": "IGN",
                "provincia_nombre": "Entre Ríos",
                "provincia_id": "30",
                "departamento_id": "30113",
                "municipio_nombre": null
            }
        }
    ]
}
```
