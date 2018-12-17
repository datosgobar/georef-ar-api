# Operaciones con Geometrías
La API permite a los usuarios operar con las geometrías de distintas entidades geográficas. A continuación, se detallan los recursos y parámetros que permiten a los usuarios realizar estas operaciones.

## Parámetro `interseccion`
Los recursos `/departamentos` y `/municipios` cuentan con el parámetro `interseccion`. El parámetro permite buscar entidades utilizando intersección de geometrías como filtro. El parámetro debe tomar valores con el siguiente formato:

	interseccion=<nombre de entidad>:<id 1>[:<id 2>:...]

Al aplicar el filtro `interseccion`, se buscan entidades que compartan área con cualquiera de las entidades listadas en la lista de IDs. Entonces, utilizar (por ejemplo) `/municipios?interseccion=departamento:18105` buscaría todos los municipios que interseccionen con el departamento con ID 18105, mientras que utilizar `/departamentos?interseccion=municipio:620133:540378` buscaría todos los departamentos que interseccionen con el municipio con ID 620133 **o** el municipio con ID 540378.

!!! note ""
	Todos los IDs listados que no correspondan a una entidad geográfica existente serán ignorados.

Ejemplo completo de llamado a la API:

`GET` [`https://apis.datos.gob.ar/georef/api/municipios?interseccion=departamento:18105`](https://apis.datos.gob.ar/georef/api/municipios?interseccion=departamento:18105)
```json
{
    "municipios": [
        {
            "centroide": {
                "lat": -28.508559,
                "lon": -58.031593
            },
            "id": "180042",
            "nombre": "Concepción",
            "provincia": {
                "id": "18",
                "nombre": "Corrientes"
            }
        },
		{ ... } // 9 resultados omitidos
    ],
    "cantidad": 10,
    "total": 13,
    "inicio": 0
}
```

## Recurso `/ubicacion`
En la [sección de inicio](/), se dió un ejemplo de uso del recurso `/ubicacion` para enriquecer datos existentes. El recurso utiliza las geometrías de las entidades geográficas para determinar cuáles contienen al punto especificado por el usuario a través de los parámetros `lat` y `lon`. Las entidades devueltas son las siguientes:

- Provincia
- Departamento
- Municipio *(opcional)*

Dependiendo del punto elegido, es posible no obtener un municipio como parte de la respuesta de la API. Como ejemplo, se muestran dos llamados distintos al recurso `/ubicacion`.

Con municipio:

`GET`[`https://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529)
```json
{
    "ubicacion": {
        "departamento": {
            "id": "10035",
            "nombre": "Belén"
        },
        "lat": -27.2741,
        "lon": -66.7529,
        "municipio": {
            "id": "100077",
            "nombre": "Hualfín"
        },
        "provincia": {
            "id": "10",
            "nombre": "Catamarca"
        }
    }
}
```

Sin municipio:

`GET`[`https://apis.datos.gob.ar/georef/api/ubicacion?lat=-28.504&lon=-62.898`](https://apis.datos.gob.ar/georef/api/ubicacion?lat=-28.504&lon=-62.898)
```json
{
    "ubicacion": {
        "departamento": {
            "id": "86028",
            "nombre": "Avellaneda"
        },
        "lat": -28.504,
        "lon": -62.898,
        "municipio": {
            "id": null,
            "nombre": null
        },
        "provincia": {
            "id": "86",
            "nombre": "Santiago del Estero"
        }
    }
}
```
