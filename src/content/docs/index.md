---
title: "API del Servicio de Normalización de Datos Geográficos de Argentina"
---

**Versión actual de la API**: 2.1

La API Georef te permite normalizar y codificar los nombres de las unidades territoriales de la Argentina (provincias, departamentos, gobiernos locales, localidades y asentamientos), de sus calles y direcciones, y ubicar coordenadas dentro de ellas. Desde la v2.0 también expone unidades geoestadísticas del INDEC (aglomerados, fracciones y radios censales), cuadras y establecimientos educativos y universitarios.

En la [Guía para la identificación y uso de entidades interoperables](https://datosgobar.github.io/paquete-apertura-datos/guia-interoperables/) se explica cómo funcionan las unidades territoriales internas de la Argentina y la relación entre ellas.

:::caution[La v1.0 está deprecada]
La documentación de la v1.0 quedó archivada en [/georef-ar-api/v1/](/georef-ar-api/v1/). Si todavía la usás, mirá la guía para [migrar desde v1.0](/georef-ar-api/migrar-desde-v1/).
:::

:::caution[Siempre indicá la versión en la URL]
La URL base de la versión actual es `https://apis.datos.gob.ar/georef/api/v2.1/`. La URL sin versión (`https://apis.datos.gob.ar/georef/api/`) **todavía responde con la v1.0**, así que todos los ejemplos de esta documentación usan `/v2.1/` de forma explícita.
:::

## Normalizar

Las unidades territoriales tienen nombres y códigos oficiales. Cuando no se usan, los datos son difíciles de cruzar entre sí y hay que normalizarlos antes.

| provincia |
| --- |
| Santiago del Estero |
| Stgo. del Estero |
| S. del Estero |
| Sgo. del Estero |

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=Sgo. del Estero`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?nombre=Sgo.%20del%20Estero)

```json
{
    "cantidad": 1,
    "inicio": 0,
    "parametros": { ... },
    "provincias": [
        {
            "centroide": {
                "lat": -27.783431882,
                "lon": -63.252626886
            },
            "id": "86",
            "nombre": "Santiago del Estero"
        }
    ],
    "total": 1
}
```

## Enriquecer

Cuando un conjunto de datos tiene coordenadas dentro de la Argentina, podés cruzarlo con muchos otros datos si le agregás las unidades territoriales que contienen cada punto.

| lat | lon |
| --- | --- |
| -27.2741 | -66.7529 |
| -34.6037389 | -58.3815704 |

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529`](https://apis.datos.gob.ar/georef/api/v2.1/ubicacion?lat=-27.2741&lon=-66.7529)

```json
{
    "parametros": { ... },
    "ubicacion": {
        "departamento": {
            "id": "10035",
            "nombre": "Belén"
        },
        "gobierno_local": {
            "id": "100077",
            "nombre": "Hualfín"
        },
        "lat": -27.2741,
        "lon": -66.7529,
        "provincia": {
            "id": "10",
            "nombre": "Catamarca"
        }
    }
}
```

## Referencia

También podés usar la API como fuente de referencia cuando creás datos vinculados a unidades territoriales. Por ejemplo, si tenés un formulario que muestra un listado de provincias y, según la provincia elegida, un listado de gobiernos locales, podés hacer estas consultas:

Listar las provincias:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/provincias?campos=id,nombre`](https://apis.datos.gob.ar/georef/api/v2.1/provincias?campos=id,nombre)

```json
{
    "cantidad": 24,
    "inicio": 0,
    "parametros": { ... },
    "provincias": [
        {
            "id": "02",
            "nombre": "Ciudad Autónoma de Buenos Aires"
        },
        { ... } // 23 resultados omitidos
    ],
    "total": 24
}
```

Si la persona elige **Chaco** (ID **22**), pedís sus gobiernos locales:

`GET` [`https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?provincia=22&campos=id,nombre&max=100`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?provincia=22&campos=id,nombre&max=100)

```json
{
    "cantidad": 70,
    "gobiernos_locales": [
        {
            "id": "220280",
            "nombre": "Pampa Almirón"
        },
        { ... } // 69 resultados omitidos
    ],
    "inicio": 0,
    "parametros": { ... },
    "total": 70
}
```

Como son datos que cambian poco, podés guardar una copia y reutilizarla.

## Límites de uso

Al 25 de septiembre de 2026, los encabezados `x-ratelimit-*` de la v2.1 informan estas cuotas por cliente: 10 pedidos por segundo, 40 por minuto, 2.000 por hora y 10.000 por día. Para normalizar muchos datos, usá las [consultas por lotes](/georef-ar-api/bulk/), que resuelven hasta 1.000 consultas en un solo pedido.

## Más información

- [Ejemplos de uso](/georef-ar-api/quick-start/)
- [Referencia de la API v2.1](/georef-ar-api/referencia/) (generada desde la especificación OpenAPI)
- [Migrar desde v1.0](/georef-ar-api/migrar-desde-v1/)

---

*Si usás la API y querés enterarte de cambios y novedades, [inscribite en la base de contactos de Datos Argentina](https://bit.ly/contacto-datos-argentina) y elegí sobre qué temas querés que te escribamos.*

*¿Tenés algo para contarnos? Escribinos por [Twitter](https://twitter.com/datosgobar) o por [mail](mailto:datosargentina@jefatura.gob.ar) y contanos cómo usás la API y qué le falta.*
