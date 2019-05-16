# Ejemplos de uso

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
    "inicio": 0,
    "parametros": { ... }
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
    "inicio": 0,
    "parametros": { ... }
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
    "inicio": 0,
    "parametros": { ... }
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
    "inicio": 0,
    "parametros": { ... }
}
```

### Normalización de direcciones
`GET` [`https://apis.datos.gob.ar/georef/api/direcciones?departamento=merlo&direccion=Florida al 2950`](https://apis.datos.gob.ar/georef/api/direcciones?departamento=merlo&direccion=Florida%20al%202950)
```
{
    "direcciones": [
		{
			"altura": {
				"unidad": null,
				"valor": 2950
			},
			"calle": {
				"categoria": "CALLE",
				"id": "0653901002985",
				"nombre": "FLORIDA"
			},
			"calle_cruce_1": {
				"categoria": null,
				"id": null,
				"nombre": null
			},
			"calle_cruce_2": {
				"categoria": null,
				"id": null,
				"nombre": null
			},
			"departamento": {
				"id": "06539",
				"nombre": "Merlo"
			},
            "localidad_censal": {
                "id": "06539010",
                "nombre": "Merlo"
            },
			"nomenclatura": "FLORIDA 2950, Merlo, Buenos Aires",
			"piso": null,
			"provincia": {
				"id": "06",
				"nombre": "Buenos Aires"
			},
			"ubicacion": {
				"lat": -34.71409079053823,
				"lon": -58.73469942899891
			}
		}
    ],
    "cantidad": 1,
    "total": 1,
    "inicio": 0,
    "parametros": { ... }
}
```

### Listado de calles
`GET` [`https://apis.datos.gob.ar/georef/api/calles?departamento=rio chico&categoria=avenida`](https://apis.datos.gob.ar/georef/api/calles?departamento=rio chico&categoria=avenida)
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
            "localidad_censal": {
                "id": "90077010",
                "nombre": "Aguilares"
            },
            "id": "9007701000050",
            "nombre": "AV GRL SAVIO",
            "nomenclatura": "AV GRL SAVIO, Río Chico, Tucumán",
            "provincia": {
                "id": "90",
                "nombre": "Tucumán"
            },
            "categoria": "AV"
        },
		{ ... } // 2 resultados omitidos
    ],
    "cantidad": 3,
    "total": 3,
    "inicio": 0,
    "parametros": { ... }
}
```
