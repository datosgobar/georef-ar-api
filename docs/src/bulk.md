# Consutas por lotes

Todos los recursos de la API tienen una variante `POST` que permite realizar varias consultas en una misma petición. De esta forma, se pueden envíar más consultas en menos tiempo. Las versiones de los recursos `POST` aceptan los mismos parámetros que las `GET`, con la excepción del parámetro `formato`, que obligatoriamente toma el valor `json`. Adicionalmente, todos los parámetros se envían a través del cuerpo de la consulta HTTP, y no como parte del *query string*.

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
            "nombre": "cordoba",
            "campos": "nombre"
        },
        {
            "nombre": "chaco",
            "campos": "nombre"
        },
        {
            "nombre": "san luis",
            "campos": "nombre"
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
            "total": 1,
            "parametros": { ... }
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
            "total": 1,
            "parametros": { ... }
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
            "total": 1,
            "parametros": { ... }
        }
    ]
}
```

Como se muestra en el ejemplo, la respuesta contiene una lista `resultados`, con los resultados de cada consulta individual adentro. Las estructuras de las respuestas se mantienen idénticas que los recursos `GET`.

!!! warning "Cantidad máxima de consultas y resultados"
    
	La cantidad de consultas en una misma petición no debe superar las 1000.

	Adicionalmente, el total de los parámetros `max` sumados de todas las consultas no debe superar los 5000.
	Por ejemplo, se permite enviar 1000 consultas con `"max": 5`, o 100 consultas con `"max": 50`, pero no 1000 consultas con `"max": 10`.

	
Utilizando los recursos por lotes, se pueden normalizar mayores cantidades de datos en menos tiempo. Por ejemplo, si se cuenta con 50000 direcciones, tan solo se necesitan 10 consultas para normalizar el activo de datos entero. Utilizando los recursos `GET`, se necesitarían 50000 (una por dato).

!!! tip "Mejor resultado por consulta"

	El uso más común de las consultas por lotes es normalizar una lista de datos, donde cada dato es una consulta. Ya que la API ordena los resultados de más acertados a menos acertados por defecto, **es recomendable agregar** `"max": 1` **a los parámetros de todas las consultas**, para obtener exclusivamente el mejor resultado por cada dato de la lista. Esto reduce la cantidad de datos transmitidos y mejora los tiempos de respuesta.

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
            "inicio": 0,
            "parametros": { ... }
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
            "inicio": 0,
            "parametros": { ... }
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
            "campos": "basico"
        },
        {
            "direccion": "corientes 4010",
            "max": 1,
			"campos": "basico",
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
            "cantidad": 1,
            "direcciones": [
                {
                    "altura": {
                        "valor": 3100
                    },
                    "calle": {
                        "id": "0642701011435",
                        "nombre": "SANTA FE"
                    },
                    "calle_cruce_1": {
                        "id": null,
                        "nombre": null
                    },
                    "calle_cruce_2": {
                        "id": null,
                        "nombre": null
                    },
                    "nomenclatura": "SANTA FE 3100, La Matanza, Buenos Aires"
                }
            ],
            "inicio": 0,
            "total": 29,
            "parametros": { ... }
        },
        {
            "cantidad": 1,
            "direcciones": [
                {
                    "altura": {
                        "valor": 4010
                    },
                    "calle": {
                        "id": "8204229000610",
                        "nombre": "CORRIENTES"
                    },
                    "calle_cruce_1": {
                        "id": null,
                        "nombre": null
                    },
                    "calle_cruce_2": {
                        "id": null,
                        "nombre": null
                    },
                    "nomenclatura": "CORRIENTES 4010, General López, Santa Fe"
                }
            ],
            "inicio": 0,
            "total": 1,
            "parametros": { ... }
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
    "resultados":  [
        {
            "ubicacion":  {
                "departamento":  {
                    "fuente":  "Adm.  Grl.  de  Catastro",
                    "id":  "10035",
                    "nombre":  "Belén"
                },
                "lat":  -27.274161,
                "lon":  -66.752929,
                "municipio":  {
                    "fuente":  "Adm.  Grl.  de  Catastro",
                    "id":  "100077",
                    "nombre":  "Hualfín"
                },
                "provincia":  {
                    "fuente":  "IGN",
                    "id":  "10",
                    "nombre":  "Catamarca"
                }
            },
            "parametros":  {  ...  }
        },
        {
            "ubicacion":  {
                "departamento_fuente":  "ATER  -  Direc.  de  Catastro",
                "departamento_id":  "30113",
                "departamento_nombre":  "Villaguay",
                "lat":  -31.480693,
                "lon":  -59.092813,
                "municipio_fuente":  null,
                "municipio_id":  null,
                "municipio_nombre":  null,
                "provincia_fuente":  "IGN",
                "provincia_id":  "30",
                "provincia_nombre":  "Entre  Ríos"
            }
            "parametros":  {  ...  }
        }
    ]
}
```
