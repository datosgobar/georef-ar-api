---
title: "Consultas por lotes"
---

Casi todos los recursos de la API tienen una variante `POST` que resuelve varias consultas en un mismo pedido, así mandás más consultas en menos tiempo. La única excepción es `/establecimientos-cercanos`, que solo acepta `GET`.

Los recursos `POST` aceptan los mismos parámetros que los `GET`, salvo `formato`, que siempre es `json`. Los parámetros van en el cuerpo del pedido HTTP (JSON), no en la *query string*. La clave de la lista es el nombre del recurso con guion bajo: `provincias`, `gobiernos_locales`, `direcciones`, `ubicaciones`, etc.

Por ejemplo, estas tres consultas:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=cordoba&campos=nombre`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=cordoba&campos=nombre)

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=chaco&campos=nombre`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=chaco&campos=nombre)

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=san luis&campos=nombre`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=san%20luis&campos=nombre)

Equivalen a esta consulta `POST` por lotes:

```bash
curl -X POST "https://apis.datos.gob.ar/georef/api/v2.1/provincias" \
  -H 'Content-Type: application/json' -d '
{
    "provincias": [
        { "nombre": "cordoba", "campos": "nombre" },
        { "nombre": "chaco", "campos": "nombre" },
        { "nombre": "san luis", "campos": "nombre" }
    ]
}'
```

Respuesta:

```json
{
    "resultados": [
        {
            "cantidad": 1,
            "inicio": 0,
            "parametros": { ... },
            "provincias": [
                { "id": "14", "nombre": "Córdoba" }
            ],
            "total": 1
        },
        {
            "cantidad": 1,
            "inicio": 0,
            "parametros": { ... },
            "provincias": [
                { "id": "22", "nombre": "Chaco" }
            ],
            "total": 1
        },
        {
            "cantidad": 1,
            "inicio": 0,
            "parametros": { ... },
            "provincias": [
                { "id": "74", "nombre": "San Luis" }
            ],
            "total": 1
        }
    ]
}
```

La respuesta trae una lista `resultados` con el resultado de cada consulta, en el mismo orden. Cada resultado tiene la misma estructura que la respuesta del recurso `GET`.

:::caution[Cantidad máxima de consultas y resultados]
Un pedido puede tener hasta 1000 consultas.

Además, la suma de los `max` de todas las consultas no puede superar 5000. Por ejemplo, podés mandar 1000 consultas con `"max": 5` o 100 con `"max": 50`, pero no 1000 con `"max": 10`.
:::

Con los lotes normalizás mucho más rápido: 50.000 direcciones con `"max": 1` entran en 50 pedidos de 1000 consultas, contra 50.000 pedidos `GET`. Tené en cuenta además la [cuota de pedidos](/georef-ar-api/#límites-de-uso) de la v2.1.

:::note[Mejor resultado por consulta]
El uso más común es normalizar una lista de datos, donde cada dato es una consulta. Como la API ordena los resultados del más al menos acertado, **agregá** `"max": 1` **a cada consulta** para quedarte solo con el mejor resultado. Así transferís menos datos y la respuesta llega más rápido.
:::

## Ejemplos

La sección [Usar en Python](/georef-ar-api/python-usage/) tiene más ejemplos de los recursos `POST`.

### Gobiernos locales en lotes

```bash
curl -X POST "https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales" \
  -H 'Content-Type: application/json' -d '
{
    "gobiernos_locales": [
        { "nombre": "belgrano", "max": 1, "campos": "id, nombre" },
        { "nombre": "martin", "max": 1, "provincia": "la pampa", "aplanar": true }
    ]
}'
```

Respuesta:

```json
{
    "resultados": [
        {
            "cantidad": 1,
            "gobiernos_locales": [
                { "id": "908224", "nombre": "Villa Belgrano" }
            ],
            "inicio": 0,
            "parametros": { ... },
            "total": 7
        },
        {
            "cantidad": 1,
            "gobiernos_locales": [
                {
                    "centroide_lat": -35.360578027,
                    "centroide_lon": -64.292331409,
                    "id": "420126",
                    "nombre": "Embajador Martini",
                    "provincia_id": "42",
                    "provincia_nombre": "La Pampa"
                }
            ],
            "inicio": 0,
            "parametros": { ... },
            "total": 2
        }
    ]
}
```

### Direcciones en lotes

```bash
curl -X POST "https://apis.datos.gob.ar/georef/api/v2.1/direcciones" \
  -H 'Content-Type: application/json' -d '
{
    "direcciones": [
        { "direccion": "santa fe 3100", "max": 1, "campos": "basico" },
        { "direccion": "corrientes 4010", "max": 1, "campos": "basico", "departamento": "General López" }
    ]
}'
```

Respuesta:

```json
{
    "resultados": [
        {
            "cantidad": 1,
            "direcciones": [
                {
                    "altura": { "valor": 3100 },
                    "calle": { "id": "380631800003020", "nombre": "SANTA FE" },
                    "calle_cruce_1": { "id": null, "nombre": null },
                    "calle_cruce_2": { "id": null, "nombre": null },
                    "nomenclatura": "SANTA FE 3100, San Pedro, San Pedro, Jujuy"
                }
            ],
            "inicio": 0,
            "parametros": { ... },
            "total": 6922
        },
        {
            "cantidad": 1,
            "direcciones": [
                {
                    "altura": { "valor": 4010 },
                    "calle": { "id": "820421200000275", "nombre": "CORRIENTES" },
                    "calle_cruce_1": { "id": null, "nombre": null },
                    "calle_cruce_2": { "id": null, "nombre": null },
                    "nomenclatura": "CORRIENTES 4010, Firmat, General López, Santa Fe"
                }
            ],
            "inicio": 0,
            "parametros": { ... },
            "total": 46
        }
    ]
}
```

La primera consulta no tiene filtros y devuelve miles de candidatos: el mejor resultado puede no ser el que esperás. Siempre que puedas, sumá `provincia`, `departamento` o `localidad_censal`.

### Unidades territoriales de varios puntos

```bash
curl -X POST "https://apis.datos.gob.ar/georef/api/v2.1/ubicacion" \
  -H 'Content-Type: application/json' -d '
{
    "ubicaciones": [
        { "lat": -27.274161, "lon": -66.752929, "campos": "completo" },
        { "lat": -31.480693, "lon": -59.092813, "aplanar": true, "campos": "completo" }
    ]
}'
```

Respuesta:

```json
{
    "resultados": [
        {
            "parametros": { ... },
            "ubicacion": {
                "calle": { "fuente": null, "id": null, "nombre": null },
                "departamento": { "fuente": "IGN", "id": "10035", "nombre": "Belén" },
                "gobierno_local": { "fuente": "DPE - INDEC", "id": "100077", "nombre": "Hualfín" },
                "lat": -27.274161,
                "lon": -66.752929,
                "nomenclatura": null,
                "provincia": { "fuente": "IGN", "id": "10", "nombre": "Catamarca" }
            }
        },
        {
            "parametros": { ... },
            "ubicacion": {
                "calle_fuente": null,
                "calle_id": null,
                "calle_nombre": null,
                "departamento_fuente": "IGN",
                "departamento_id": "30113",
                "departamento_nombre": "Villaguay",
                "gobierno_local_fuente": "DPE - INDEC",
                "gobierno_local_id": "309950",
                "gobierno_local_nombre": "Mojones Norte",
                "lat": -31.480693,
                "lon": -59.092813,
                "nomenclatura": null,
                "provincia_fuente": "IGN",
                "provincia_id": "30",
                "provincia_nombre": "Entre Ríos"
            }
        }
    ]
}
```
