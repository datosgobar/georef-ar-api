# georef-api
API del servicio de normalización y geocodificación para direcciones de Argentina.

## Índice 
* [Uso de georef-api](#uso-de-georef-api)
* [Contacto](#contacto)

## Uso de georef-api

### Normalizador `/api/v1.0/normalizador`

Entrada:
- **direccion**: la dirección que se quiere normalizar (campo obligatorio).
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
      "nomenclatura": "Avenida Presidente Roque Sáenz Peña 250, 1425 Ciudad ...",
      "tipo": "Avenida",
      "nombre": "Presidente Roque Sáenz Peña",
      "altura": 250,
      "codigo_postal": 1425,
      "localidad": "Ciudad Autónoma de Buenos Aires",
      "partido": "Ciudad Autónoma de Buenos Aires",
      "provincia": "Capital Federal",
      "observaciones": {
        "fuente": "Fuente del resultado.",
        "info": "Información adicional sobre el resultado."
        }
    },
    {
      "..."
    },
  ]
}
```

### Ejemplos

Un cliente quiere saber a qué localidad corresponde una dirección dada.
En este caso, consumiría la API de búsqueda pasando los parámetros `dirección` y `provincia`.
Si la dirección existe, debería recibir uno o más resultados.

**GET** `/api/v1.0/normalizador?direccion=Echeverria+4497&provincia=Buenos+Aires`
```json
{
  "estado": "OK",
  "direcciones": [
    {
      "nomenclatura": "Esteban Echeverría 4497, 1757 Gregorio Laferrere, Buenos Aires",
      "tipo": "Calle",
      "nombre": "Esteban Echeverría",
      "altura": 4497,
      "codigo_postal": 1757,
      "localidad": "Gregorio Laferrere",
      "partido": "La Matanza",
      "provincia": "Buenos Aires",
      "observaciones": {
        "fuente": "INDEC",
        "info": "Se procesó correctamente la dirección buscada."
        }
    },
    {
      "nomenclatura": "Esteban Echeverría 4497, 1706 Villa Sarmiento, Buenos Aires",
      "tipo": "Calle",
      "nombre": "Esteban Echeverría",
      "altura": 4497,
      "codigo_postal": 1706,
      "localidad": "Villa Sarmiento",
      "partido": "Morón",
      "provincia": "Buenos Aires",
      "observaciones": {
        "fuente": "INDEC",
        "info": "Se procesó correctamente la dirección buscada."
        }
    },
    {
      "..."
    },
  ],
}
```

**Errores**

Cuando se produce un error durante el procesamiento de una consulta,
la respuesta de la API incluye el campo "error" con información detallada.
```json
{
  "codigo": 400, 
  "error": {
    "codigo_interno": null,
    "info": "https://github.com/datosgobar/georef-api",
    "mensaje": "El Request tiene parámetros inválidos o está incompleto.",
  },
  "estado": "INVALIDO"
}
```


**Normalizar lote de direcciones**

**POST** `/api/v1.0/normalizador`

Entrada:
- campos: qué campos devolver.
- **body**: JSON con lote de direcciones para normalizar.
```json
{
  "direcciones": [
    "Roque Sáenz Peña 788, Buenos Aires",
    "Calle Principal 123, 1425 CABA",
    "Esmeralda 1000, Capital Federal",
    "..."
  ]
}
```

Salida: JSON con el siguiente formato.
```json
{
  "estado": "OK",
  "direcciones": [
    {
      "original": "Roque Sáenz Peña 788, Buenos Aires",
      "normalizadas": [
        {
          "nomenclatura": "Av. Presidente Roque Sáenz Peña 788, 1035 Ciudad Autónoma ...",
          "tipo": "Avenida",
          "nombre": "Presidente Roque Sáenz Peña",
          "altura": 788,
          "codigo_postal": 1035,
          "localidad": "Ciudad Autónoma de Buenos Aires",
          "partido": "Ciudad Autónoma de Buenos Aires",
          "provincia": "Capital Federal",
          "observaciones": {
            "fuente": "INDEC",
            "info": "Se procesó correctamente la dirección buscada."
            }
        },
      ]
    },
    {
      "..."
    },
  ]
}
```

### Provincias `/api/v1.0/provincias`
Retorna un listado de provincias.

Entrada:
- nombre: para filtrar por nombre.

**GET** `/api/v1.0/provincias`
```json
{
  "estado": "OK", 
  "provincias": [
    {
      "id": "14", 
      "nombre": "Córdoba"
    }, 
    {
      "id": "22", 
      "nombre": "Chaco"
    }, 
    {
      "id": "26", 
      "nombre": "Chubut"
    }, 
    {
      "id": "06", 
      "nombre": "Buenos Aires"
    }, 
    {
      "id": "10", 
      "nombre": "Catamarca"
    },
    "..."
  ]
}
```

### Departamentos `/api/v1.0/departamentos`
Retorna un listado de departamentos.

Entrada:
- nombre: para filtrar por nombre.

**GET** `/api/v1.0/departamentos?nombre=capital`
```json
{
  "estado": "OK",
  "departamentos": [
    {
      "id": "50007", 
      "nombre": "Capital", 
      "provincia": {
        "id": "50", 
        "nombre": "Mendoza"
      }
    }, 
    {
      "id": "54028", 
      "nombre": "Capital", 
      "provincia": {
        "id": "54", 
        "nombre": "Misiones"
      }
    }, 
    {
      "id": "86049", 
      "nombre": "Capital", 
      "provincia": {
        "id": "86", 
        "nombre": "Santiago del Estero"
      }
    },
    "..."
  ]
}
```

### Localidades `/api/v1.0/localidades`
Retorna un listado de localidades.

Entrada:
- nombre: para filtrar por nombre.

**GET** `/api/v1.0/localidades`
```json
{
  "estado": "OK", 
  "localidades": [
    {
      "id": "06007080", 
      "nombre": "Rivera", 
      "departamento": {
        "id": "06007", 
        "nombre": "Adolfo Alsina"
      }, 
      "provincia": {
        "id": "06", 
        "nombre": "Buenos Aires"
      }
    }, 
    {
      "id": "06014030", 
      "nombre": "Juan E. Barra", 
      "departamento": {
        "id": "06014", 
        "nombre": "Adolfo Gonzales Chaves"
      }, 
      "provincia": {
        "id": "06", 
        "nombre": "Buenos Aires"
      }
    }, 
    {
      "id": "06021020", 
      "nombre": "Coronel Seguí", 
      "departamento": {
        "id": "06021", 
        "nombre": "Alberti"
      }, 
      "provincia": {
        "id": "06", 
        "nombre": "Buenos Aires"
      }
    },
    "..."
  ]
}
```

### Calles `/api/v1.0/calles`
Retorna calles (normalizadas) de una localidad o provincia.

Entrada:
- localidad: para filtrar por localidad.
- provincia: para filtrar por provincia.
- tipo: para filtrar por tipo de camino.

Ejemplo: obtener todas las calles de Bariloche.

**GET** `/api/v1.0/calles?localidad=Bariloche`

Salida: JSON con el siguiente formato.
```json
{
    "estado": "OK",
    "calles": [
        {
            "nomenclatura": "Avenida 12 de Octubre, 8400 San Carlos de Bariloche, Río Negro",
            "tipo": "Avenida",
            "uri": ".../api/v1.0/calles/1"
        },
        {
            "nomenclatura": "Diagonal 1, 8400 San Carlos de Bariloche, Río Negro",
            "tipo": "Calle",
            "uri": ".../api/v1.0/calles/2"
        },
        {
            "..."
        },
    ],
}
```

**GET** `/api/v1.0/calles/{id}`

Retorna detalles de una calle particular.
```json
{
    "estado": "OK",
    "id": 1,
    "nomenclatura": "Avenida 12 de Octubre, 8400 San Carlos de Bariloche, Río Negro",
    "nombre": "12 de Octubre",
    "tipo": "Avenida",
    "altura": {
        "inicial": 1,
        "final": 99
    },
    "localidad": "San Carlos de Bariloche",
    "provincia": "Río Negro",
    "geom": "Ax0BF543E..."
}
```

### Geocodificador `/api/v1.0/geocodificador`


## Contacto
Te invitamos a [crearnos un issue](https://github.com/datosgobar/georef-api/issues/new?title=Encontre-un-bug-en-georef-api) en caso de que encuentres algún bug o tengas comentarios     de alguna parte de `georef-api`. Para todo lo demás, podés mandarnos tu sugerencia o consulta a [datos@modernizacion.gob.ar](mailto:datos@modernizacion.gob.ar).