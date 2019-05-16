# Localidades y asentamientos

Entre los distintos tipos de entidades geográficas que maneja la API, se encuentran las **localidades censales**, las **localidades** y los **asentamientos**. A continuación se explica en detalle la definición de cada una de estas entidades.

## Localidades censales
El listado de **localidades censales** proviene de [INDEC](https://www.indec.gov.ar/codgeo.asp). Las localidades censales son unidades geoestadísticas elaboradas por INDEC para los censos nacionales.

El recurso correspondiente de la API es [`/localidades-censales`](https://apis.datos.gob.ar/georef/api/localidades-censales).

## Localidades
Las **localidades** (a no ser confundidas con las localidades censales) provienen de [BAHRA](http://www.bahra.gob.ar/). La base BAHRA identifica localidades, parajes y sitios edificados de la República Argentina con un nombre y un código único.

El listado de localidades se contruye a partir de un **subconjunto de BAHRA**. Nosotros consideramos que **este subconjunto es el que mejor representa el concepto general de "localidad", el cual no tiene definición formal**.

Notar que todas las localidades pertenecen a una localidad censal.

El recurso correspondiente de la API es [`/localidades`](https://apis.datos.gob.ar/georef/api/localidades).

## Asentamientos
Los **asentamientos** también provienen de BAHRA. Sin embargo, el listado de asentamientos se contruye a partir de la **enteridad de BAHRA**. Esto implica que todas las entidades del listado de localidades están incluidas en el listado de asentamientos. El listado de asentamientos, sin embargo, contiene entidades que en general un usuario no consideraría ser una "localidad".

Notar que los asentamientos **opcionalmente** pueden pertenecer a una localidad censal.

El recurso correspondiente de la API es [`/asentamientos`](https://apis.datos.gob.ar/georef/api/asentamientos).
