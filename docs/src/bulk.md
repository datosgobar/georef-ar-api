# Consutas por lotes

Todos los recursos de la API tienen una variante `POST` que permite realizar varias consultas en una misma petición. De esta forma, se pueden envíar más consultas en menos tiempo. Las versiones de los recursos `POST` aceptan los mismos parámetros que las `GET`, con la excepción del parámetro `formato`, que necesariamente toma el valor `json`. Adicionalmente, todos los parámetros se envían a través del cuerpo de la consulta HTTP, y no como parte del *query string*.

Por ejemplo, las siguientes tres consultas:

`GET` [`https://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba&campos=nombre`](https://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba&campos=nombre)

`GET` [`https://apis.datos.gob.ar/georef/api/provincias?nombre=chaco&campos=nombre`](https://apis.datos.gob.ar/georef/api/provincias?nombre=chaco&campos=nombre)

`GET` [`https://apis.datos.gob.ar/georef/api/provincias?nombre=san luis&campos=nombre`](https://apis.datos.gob.ar/georef/api/provincias?nombre=san luis&campos=nombre)

Son equivalentes a la siguiente consulta `POST` por lotes:

`POST` `https://apis.datos.gob.ar/georef/api/provincias`
```json
{
    "provincias": [
        {
            "nombre": "cordoba"
        },
        {
            "nombre": "chaco"
        },
        {
            "nombre": "san luis"
        }
    ]
}
```

Que resultaría en la siguiente respuesta JSON:
```json
{
    "resultados": [
        {
            "cantidad": 1,
            "inicio": 0,
            "provincias": [
                {
                    "id": "14",
                    "nombre": "Córdoba"
                }
            ],
            "total": 1
        },
        {
            "cantidad": 1,
            "inicio": 0,
            "provincias": [
                {
                    "id": "22",
                    "nombre": "Chaco"
                }
            ],
            "total": 1
        },
        {
            "cantidad": 1,
            "inicio": 0,
            "provincias": [
                {
                    "id": "74",
                    "nombre": "San Luis"
                }
            ],
            "total": 1
        }
    ]
}
```

Como se muestra en el ejemplo, la respuesta contiene una lista `resultados`, con los resultados de cada consulta individual adentro. Las estructuras de las respuestas se mantienen idénticas que los recursos `GET`.

!!! note ""
    
	El total de los parámetros `max` sumados de todas las consultas no debe superar los 5000.
	Por ejemplo, se permite enviar 5000 consultas con `max=1`, o 100 consultas con `max=50`, pero no 5000 consultas con `max=10`.
	
Utilizando los recursos por lotes, se pueden normalizar mayores cantidades de datos en menos tiempo. Por ejemplo, si se cuenta con 50000 direcciones, tan solo se necesitan 10 consultas para normalizar el activo de datos entero. Utilizando los recursos `GET`, se necesitarían 50000 (una por dato).

## Ejemplos de uso

A diferencia de los recursos `GET`, los ejemplos de operaciones por lotes se muestran utilizando comandos construídos sobre la herramienta `curl`. La sección de [ejemplos con Python](python-usage.md) también contiene ejemplos de uso de los recursos `POST`.

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
