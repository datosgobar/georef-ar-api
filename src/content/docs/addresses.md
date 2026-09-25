---
title: "Normalización de direcciones"
---

El recurso `/direcciones` normaliza y georreferencia direcciones de calles. Como el resto de los recursos, tiene filtros y opciones para controlar los resultados.

## Parámetros y filtros

El único parámetro obligatorio es `direccion`: una combinación de nombres de calles y una altura, preferentemente numérica. La API tolera direcciones con distintas estructuras e intenta interpretar qué representa cada parte del texto, teniendo en cuenta errores de escritura comunes. Para eso usa la librería [georef-ar-address](https://github.com/datosgobar/georef-ar-address). Como a veces la estructura no se puede interpretar bien, te recomendamos usar alguno de estos formatos:

- **calle** [altura]
- **calle 1** [altura] *esquina/y* **calle 2**
- **calle 1** *esquina/y* **calle 2** [altura]
- **calle 1** [altura] *entre* **calle 2** y **calle 3**
- **calle 1** *entre* **calle 2** y **calle 3** [altura]

En todos los casos la [altura] es opcional y, si está, puede ir seguida de un piso o departamento.

Para obtener resultados más precisos, sumá los filtros `provincia`, `departamento`, `localidad_censal` y/o `localidad`. El parámetro `desplazar` mueve el punto georreferenciado del eje de la calle hacia la manzana (ver más abajo). El resto de los parámetros está en la [referencia de la API](/georef-ar-api/referencia/).

## Campos de respuesta

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av. Santa Fe nro 260 2ndo C, entre Santa Rosa y Colón&departamento=capital&provincia=cordoba`](https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av.%20Santa%20Fe%20nro%20260%202ndo%20C,%20entre%20Santa%20Rosa%20y%20Col%C3%B3n&departamento=capital&provincia=cordoba)

```json
{
    "cantidad": 1,
    "direcciones": [
        {
            "altura": {
                "unidad": "nro",
                "valor": 260
            },
            "calle": {
                "categoria": "AV",
                "id": "140140100002460",
                "nombre": "AV SANTA FE"
            },
            "calle_cruce_1": {
                "categoria": "CALLE",
                "id": "140140100038100",
                "nombre": "SANTA ROSA"
            },
            "calle_cruce_2": {
                "categoria": "AV",
                "id": "140140100002060",
                "nombre": "AV COLON"
            },
            "departamento": {
                "id": "14014",
                "nombre": "Capital"
            },
            "localidad": {
                "id": null,
                "nombre": null
            },
            "localidad_censal": {
                "id": "14014010",
                "nombre": "Córdoba"
            },
            "nomenclatura": "AV SANTA FE 260 (ENTRE SANTA ROSA Y AV COLON), Córdoba, Capital, Córdoba",
            "piso": "2ndo C",
            "provincia": {
                "id": "14",
                "nombre": "Córdoba"
            },
            "ubicacion": {
                "lat": -31.40777788475033,
                "lon": -64.20051568344584
            }
        }
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 1
}
```

Los campos estándar son:

- `altura`
    - `unidad`: unidad de la altura o prefijo del valor numérico.
    - `valor`: valor numérico de la altura, o `null` si la altura no es numérica.
- `calle`: primera calle de la dirección (**calle 1**): `nombre` normalizado, `id` (15 dígitos) y `categoria`.
- `calle_cruce_1`: segunda calle (**calle 2**), si la hay. Mismos subcampos.
- `calle_cruce_2`: tercera calle (**calle 3**), si la hay. Mismos subcampos.
- `provincia`, `departamento`, `localidad_censal`: unidades que contienen a la **calle 1**.
- `localidad`: localidad (BAHRA) de la **calle 1**, si se pudo determinar. Es nuevo en la v2.
- `piso`: piso o departamento extraído de la dirección.
- `nomenclatura`: versión normalizada de la dirección.
- `ubicacion`: resultado de la georreferenciación (`lat` y `lon`). Es una **aproximación**; si falta, es porque los datos disponibles no alcanzaron para estimarla. La efectividad varía según la región del país.

## Parámetro `desplazar`

Por defecto el punto cae sobre el eje de la calle. Con `desplazar=true`, la API lo corre unos metros hacia la manzana, del lado de la cuadra que corresponde a la paridad (par o impar) de la altura. Con la misma dirección de arriba, sin y con `desplazar`:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av. Santa Fe 260&departamento=capital&provincia=cordoba&max=1&campos=nomenclatura,ubicacion`](https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av.%20Santa%20Fe%20260&departamento=capital&provincia=cordoba&max=1&campos=nomenclatura,ubicacion)

```json
"ubicacion": {
    "lat": -31.40777788475033,
    "lon": -64.20051568344584
}
```

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av. Santa Fe 260&departamento=capital&provincia=cordoba&max=1&campos=nomenclatura,ubicacion&desplazar=true`](https://apis.datos.gob.ar/georef/api/v2.1/direcciones?direccion=Av.%20Santa%20Fe%20260&departamento=capital&provincia=cordoba&max=1&campos=nomenclatura,ubicacion&desplazar=true)

```json
"ubicacion": {
    "lat": -31.407807058305238,
    "lon": -64.20041621039096
}
```

## Normalización por lotes

Para normalizar muchas direcciones, usá las [consultas por lotes](/georef-ar-api/bulk/).
