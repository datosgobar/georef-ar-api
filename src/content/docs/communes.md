---
title: "Comunas de CABA"
---

Las 15 comunas de la Ciudad Autónoma de Buenos Aires (CABA) aparecen en tres recursos de la v2.1, cada uno con su propio ID:

- `/departamentos`: IDs de 5 dígitos definidos por la [Resolución 55/2019 del INDEC](https://www.boletinoficial.gob.ar/detalleAviso/primera/203487/20190318).
- `/gobiernos-locales`: IDs de 6 dígitos, con `categoria` "Comuna".
- `/localidades-censales`: una localidad censal por comuna, llamada "CABA - Comuna N" (IDs de 8 dígitos).

| Comuna | Departamento | Gobierno local | Localidad censal |
| --- | --- | --- | --- |
| Comuna 1 | 02007 | 022007 | 02007010 |
| Comuna 2 | 02014 | 022014 | 02014010 |
| Comuna 3 | 02021 | 022021 | 02021010 |
| Comuna 4 | 02028 | 022028 | 02028010 |
| Comuna 5 | 02035 | 022035 | 02035010 |
| Comuna 6 | 02042 | 022042 | 02042010 |
| Comuna 7 | 02049 | 022049 | 02049010 |
| Comuna 8 | 02056 | 022056 | 02056010 |
| Comuna 9 | 02063 | 022063 | 02063010 |
| Comuna 10 | 02070 | 022070 | 02070010 |
| Comuna 11 | 02077 | 022077 | 02077010 |
| Comuna 12 | 02084 | 022084 | 02084010 |
| Comuna 13 | 02091 | 022091 | 02091010 |
| Comuna 14 | 02098 | 022098 | 02098010 |
| Comuna 15 | 02105 | 022105 | 02105010 |

Los IDs salen de estas consultas (25/09/2026):

- [`/v2.1/departamentos?provincia=02&campos=id,nombre&max=20&orden=id`](https://apis.datos.gob.ar/georef/api/v2.1/departamentos?provincia=02&campos=id,nombre&max=20&orden=id)
- [`/v2.1/gobiernos-locales?provincia=02&campos=id,nombre,categoria&max=20&orden=id`](https://apis.datos.gob.ar/georef/api/v2.1/gobiernos-locales?provincia=02&campos=id,nombre,categoria&max=20&orden=id)
- [`/v2.1/localidades-censales?provincia=02&campos=id,nombre&max=20&orden=id`](https://apis.datos.gob.ar/georef/api/v2.1/localidades-censales?provincia=02&campos=id,nombre&max=20&orden=id)

:::note[Cambio respecto de v1.0]
En la v1.0, CABA tenía una sola localidad censal para toda la ciudad. En la v2.1 hay una por comuna.
:::
