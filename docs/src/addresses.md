# Normalización de Direcciones

El recurso `/direcciones` de la API permite normalizar y georreferenciar direcciones de calles. Como todos los otros recursos, cuenta con varios filtros y opciones que permiten controlar los resultados obtenidos.

## Parámetros y filtros

El único parámetro obligatorio del recurso `/direcciones` es `direccion`. El mismo debe tomar el valor de una dirección: es decir, una combinación de nombres de calles y una altura preferiblemente numérica. La API tolera direcciones con distintas estructuras, y se hace un esfuerzo en intentar interpretar qué información representa cada parte del valor recibido, teniendo en cuenta errores de escritura comunes. Para lograr esto, se utiliza la librería [georef-ar-address](https://github.com/datosgobar/georef-ar-address). En algunos casos, la estructura de la dirección no puede ser interpretada correctamente; para evitar estos casos se recomienda utilizar direcciones con el siguiente formato aproximado:

- **calle** [altura]
- **calle 1** [altura] *esquina/y* **calle 2**
- **calle 1** *esquina/y* **calle 2** [altura]
- **calle 1** [altura] *entre* **calle 2** y **calle 3**
- **calle 1** *entre* **calle 2** y **calle 3** [altura]

En todos los casos, el valor [altura] es opcional, y de estar presente puede ser seguido de un piso/número de departamento.

El resto de los parámetros aceptados por el recurso `/direccion` están listados en la [referencia completa de la API](https://datosgobar.github.io/georef-ar-api/open-api). Se recomienda utilizar los parámetros `provincia`, `departamento`, `localidad_censal` y/o `localidad` para obtener resultados más precisos.

## Campos de respuesta

Al normalizar una dirección, la API devuelve varios campos de datos. Para entender el significado de cada uno, es conveniente utilizar un ejemplo de uso:

`GET` [https://apis.datos.gob.ar/georef/api/direcciones?direccion=Av. Santa Fe nro 260 2ndo C, entre Santa Rosa y Colón&departamento=capital&provincia=cordoba](https://apis.datos.gob.ar/georef/api/direcciones?direccion=Av.%20Santa%20Fe%20nro%20260%202ndo%20C,%20entre%20Santa%20Rosa%20y%20Col%C3%B3n&departamento=capital&provincia=cordoba)
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
                "id": "1401401002460",
                "nombre": "AV SANTA FE"
            },
            "calle_cruce_1": {
                "categoria": "CALLE",
                "id": "1401401038100",
                "nombre": "SANTA ROSA"
            },
            "calle_cruce_2": {
                "categoria": "AV",
                "id": "1401401002060",
                "nombre": "AV COLON"
            },
            "departamento": {
                "id": "14014",
                "nombre": "Capital"
            },
            "localidad_censal": {
                "id": "14014010",
                "nombre": "Córdoba"
            },
            "nomenclatura": "AV SANTA FE 260 (ENTRE SANTA ROSA Y AV COLON), Capital, Córdoba",
            "piso": null,
            "provincia": {
                "id": "14",
                "nombre": "Córdoba"
            },
            "ubicacion": {
                "lat": -31.4080674840673,
                "lon": -64.20062417513701
            }
        }
    ],
    "inicio": 0,
    "total": 1,
    "parametros": { ... }
}
```

Como se puede observar, campos de respuesta estándar son:

- `altura`
	- `unidad`: Unidad de la altura, o prefijo del valor numérico de la misma.
	- `valor`: Valor numérico de la altura, o `null` si la altura ingresada no fue numérica.
- `calle`: Propiedades de la primera calle presente en la dirección.
	- `nombre`: Nombre normalizado de la **calle 1**.
	- `id`: ID de la **calle 1**.
	- `categoria`: Tipo de la **calle 1**.
- `calle_cruce_1`: Propiedades de la segunda calle presente en la dirección *(valores opcionales)*.
	- `nombre`: Nombre normalizado de la **calle 2**.
	- `id`: ID de la **calle 2**.
	- `categoria`: Tipo de la **calle 2**.
- `calle_cruce_1`: Propiedades de la tercera calle presente en la dirección *(valores opcionales)*.
	- `nombre`: Nombre normalizado de la **calle 3**.
	- `id`: ID de la **calle 3**.
	- `categoria`: Tipo de la **calle 3**.
- `departamento`: Departamento de la **calle 1**.
- `localidad_censal`: Localidad censal de la **calle 1**.
- `provincia`: Provincia de la **calle 1**.
- `piso`: Piso extraído de la dirección.
- `nomenclatura`: Versión normalizada de la dirección.
- `ubicacion`: Resultados de la georreferenciación de la dirección (`lon` y `lat`). Cuando los valores están presentes, representan una **aproximación** de la ubicación de la dirección. Cuando no están presentes, se debe a que los datos indexados en la API no fueron suficientes para obtener un resultado estimativo. La efectividad de la georreferenciación varía de acuerdo a cada región del país.

## Normalización de direcciones por lotes

Para normalizar grandes cantidades de direcciones, se recomienda utilizar los recursos de [consultas por lotes](bulk.md).
