# georef-api
API del servicio de normalización y geocodificación para direcciones de Argentina.

## Índice 
* [Uso de georef-api](#uso-de-georef-api)
* [Contacto](#contacto)

## Uso de georef-api

### Normalizar dirección
**GET**	/api/buscar?direccion={una_direccion}

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
            "descripcion": "dirección completa normalizada",
            "tipo": "Avenida",
            "nombre": "Presidente Roque Sáenz Peña",
            "altura": 250,
            "codigo_postal": 1425,
            "localidad": "Ciudad Autónoma de Buenos Aires",
            "partido": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Capital Federal",
            "tipo_resultado": "puerta"
        },
        {
            "..."
        },
    ],
    "error": "null"
}
```

### Ejemplos

Un cliente quiere saber a qué localidad corresponde una dirección dada.
En este caso, consumiría la API de búsqueda pasando los parámetros `dirección` y `provincia`.
Si la dirección existe, debería recibir uno o más resultados.

**GET** `/api/buscar?direccion=Echeverria 4497&provincia=Buenos Aires`

```json
{
    "estado": "OK",
    "direcciones": [
        {
            "descripcion": "Esteban Echeverría 4497, 1757 Gregorio Laferrere, Buenos Aires",
            "tipo": "Calle",
            "nombre": "Esteban Echeverría",
            "altura": 4497,
            "codigo_postal": 1757,
            "localidad": "Gregorio Laferrere",
            "partido": "La Matanza",
            "provincia": "Buenos Aires",
            "tipo_resultado": "puerta"
        },
        {
            "descripcion": "Esteban Echeverría 4497, 1706 Villa Sarmiento, Buenos Aires",
            "tipo": "Calle",
            "nombre": "Esteban Echeverría",
            "altura": 4497,
            "codigo_postal": 1706,
            "localidad": "Villa Sarmiento",
            "partido": "Morón",
            "provincia": "Buenos Aires",
            "tipo_resultado": "puerta"
        },
        {
            "..."
        },
    ],
}
```

Un cliente desea obtener todas las calles (normalizadas) de una localidad, sin importarle el resto de los campos.
En este caso, consumiría la API de búsqueda pasando los parámetros `localidad` y `campos`.

**GET** `/api/buscar?direccion=""&localidad=Bariloche&campos=direccion,tipo_resultado`

```json
{
    "estado": "OK",
    "direcciones": [
        {
            "descripcion": "Avenida 12 de Octubre, 8400 San Carlos de Bariloche, Río Negro",
        },
        {
            "descripcion": "Diagonal 1, 8400 San Carlos de Bariloche, Río Negro",
        },
        {
            "..."
        },
    ],
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
        "..."
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
        {
            "..."
        }
    ],
    "direcciones": [
        {
            "id_original": "1",
            "descripcion": "dirección completa normalizada",
            "tipo": "Avenida",
            "nombre": "Presidente Roque Sáenz Peña",
            "altura": 250,
            "codigo_postal": 1425,
            "localidad": "Ciudad Autónoma de Buenos Aires",
            "partido": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Capital Federal",
            "tipo_resultado": "puerta"
        },
        {
            "..."
        },
    ],
    "error": "null"
}
```

### Geocodificar dirección
**GET** /api/geocodificar


## Contacto
Te invitamos a [crearnos un issue](https://github.com/datosgobar/georef-api/issues/new?title=Encontre-un-bug-en-georef-api) en caso de que encuentres algún bug o tengas comentarios     de alguna parte de `georef-api`. Para todo lo demás, podés mandarnos tu sugerencia o consulta a [datos@modernizacion.gob.ar](mailto:datos@modernizacion.gob.ar).