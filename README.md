# georef-api
[![Build Status](https://travis-ci.org/datosgobar/georef-api.svg?branch=master)](https://travis-ci.org/datosgobar/georef-api)

API del servicio de normalización y geocodificación de direcciones para organismos de la Administración Pública Nacional.

## Documentación
Ver la [documentación completa](https://datosgobar.github.io/georef-api/) para los recursos disponibles de la API.

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
            "lat": -32.142933,
            "lon": -63.801753,
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
            "lat": -24.194923,
            "lon": -65.12645,
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

## Instalación
Si se desea contar con una instancia de Georef API propia, es necesario seguir los pasos de instalación, ya sea para entornos de desarrollo o de producción:

### Configuración para un entorno de desarrollo
Ver la [guía de instalación](docs/georef-api-development.md) para entornos de desarrollo.
### Configuración para un entorno de producción
Ver la [guía de instalación](docs/georef-api-production.md) para entornos de producción.

## Soporte
En caso de que encuentres algún bug, tengas problemas con la instalación, o tengas comentarios de alguna parte de Georef API, podés mandarnos un mail a [datos@modernizacion.gob.ar](mailto:datos@modernizacion.gob.ar) o [crear un issue](https://github.com/datosgobar/georef-api/issues/new?title=Encontre-un-bug-en-georef-api).
