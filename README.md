# georef-api
API del servicio de normalización y geocodificación para direcciones de Argentina.

## Índice 
* [Uso de georef-api](#uso-de-georef-api)
* [Contacto](#contacto)

## Uso de georef-api

### Normalizar dirección
**GET**	/api/normalizar?direccion={una_direccion}

Entrada:
- **direccion**: la dirección que se quiere normalizar; debería seguir cierto formato.
- localidad: para filtrar por localidad.
- provincia: para filtrar por provincia.
- campos: qué campos devolver.
- max: cantidad máxima esperada de sugerencias.

Salida: JSON con el siguiente formato.
```json
{
    "estado": "OK|SIN_RESULTADOS|INVALIDO",
    "direcciones": [
        {
            "direccion": "dirección completa normalizada",
            "tipo": "Avenida",
            "nombre": "Presidente Roque Sáenz Peña",
            "altura": 250,
            "codigo_postal": 1425,
            "localidad": "Ciudad Autónoma de Buenos Aires",
            "partido": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Capital Federal",
            "tipo_resultado": "puerta"
        },
        ...
    ]
    "error": null	// Sólo presente cuando el estado != OK.
}
```

### Normalizar lote de direcciones
**POST** /api/normalizar

Entrada:
- campos: qué campos devolver.
- **body**: JSON con lote de direcciones para normalizar.
```json
{
    "direcciones": [
        "Av. Roque Sáenz Peña 788, Buenos Aires",
        "Calle Principal 123, 1425 CABA",
        "Esmeralda 1000, Capital Federal",
        ...
    ]
}
```

Salida: JSON con el siguiente formato (provisorio)
```json
{
    "estado": "OK|SIN_RESULTADOS|INVALIDO",
    "orginales": [
        {
            "id": 1,
            "nombre": "Roque Sáenz Peña",
        },
        ...
    ]
    "direcciones": [
        {
            "id_original": "1",
            "direccion": "dirección completa normalizada",
            "tipo": "Avenida",
            "nombre": "Presidente Roque Sáenz Peña",
            "altura": 250,
            "codigo_postal": 1425,
            "localidad": "Ciudad Autónoma de Buenos Aires",
            "partido": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Capital Federal",
            "tipo_resultado": "puerta"
        },
        ...
    ]
    "error": null	// Sólo presente cuando el estado != OK.
}
```

### Geocodificar dirección
**GET** /api/geocodificar?


## Contacto
Te invitamos a [crearnos un issue](https://github.com/datosgobar/georef-api/issues/new?title=Encontre-un-bug-en-georef-api) en caso de que encuentres algún bug o tengas comentarios     de alguna parte de `georef-api`. Para todo lo demás, podés mandarnos tu sugerencia o consulta a [datos@modernizacion.gob.ar](mailto:datos@modernizacion.gob.ar).