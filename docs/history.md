# Historial de versiones para `georef-ar-api`

## 0.1.3
- Se modificaron los siguientes campos:
  - `centroide_lat` y `centroide_lon` ahora están anidados.
  - Los campos `altura_inicio_derecha`, `altura_fin_derecha`, etc. ahora están anidados.
- Se agregó una validación de valores repetidos para parámetro `campos`.
- El recurso `/provincias` ahora acepta el parámetro `aplanar`.

## 0.1.2
- Se removió `d` como stopword en Elasticsearch.

## 0.1.1
- Se modificaron los siguientes campos:
  - `lat` ahora es `centroide_lat`.
  - `lon` ahora es `centroide_lon`.
  - Los campos `inicio_derecha`, `fin_derecha`, etc. ahora comienzan con `altura_`.

## 0.1.0
- Versión inicial.
