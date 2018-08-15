# Comenzar a usar la API Georef

## Ejemplos
A continuación, se muestran algunos ejemplos de uso de la API:

### Búsqueda de provincias:
`GET` [`http://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba`](http://apis.datos.gob.ar/georef/api/provincias?nombre=cordoba)

```
{
    "provincias": [
        {
            "fuente": "IGN",
            "id": "14",
            "centroide_lat": -32.142933,
            "centroide_lon": -63.801753,
            "nombre": "CÓRDOBA"
        }
    ]
}
```

### Búsqueda de departamentos
`GET` [`http://apis.datos.gob.ar/georef/api/departamentos?provincia=jujuy&max=16`](http://apis.datos.gob.ar/georef/api/departamentos?provincia=jujuy&max=16)

```
{
    "departamentos": [
        {
            "fuente": "IGN",
            "id": "38042",
            "centroide_lat": -24.194923,
            "centroide_lon": -65.12645,
            "nombre": "PALPALÁ",
            "provincia": {
                "id": "38",
                "nombre": "JUJUY"
            }
        },
        { ... } // 15 departamentos omitidos
    ]
}
```

### Normalización de direcciones
`GET` [`http://apis.datos.gob.ar/georef/api/direcciones?provincia=buenos aires&direccion=Florida 1801`](http://apis.datos.gob.ar/georef/api/direcciones?provincia=buenos%20aires&direccion=Florida%201801)

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
    ]
}
```

### Entidades geográficas en un punto
`GET` [`http://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529`](http://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529)

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
