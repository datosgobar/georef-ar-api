# API del Servicio de Normalización de Datos Geográficos de Argentina

La API del Servicio de Normalización de Datos Geográficos, permite normalizar y codificar los nombres de unidades territoriales de la Argentina (provincias, departamentos, municipios y localidades) y de sus calles, así como ubicar coordenadas dentro de ellas.

Las unidades territoriales tienen nombres y códigos oficiales. Cuando no se usan, los datos son difíciles de cruzar entre sí y hay que normalizarlos antes.

<table>
    <tr><td>provincia</td></tr>
    <tr><td>Santiago del Estero</td></tr>
    <tr><td>Stgo. del Estero</td></tr>
    <tr><td>S. del Estero</td></tr>
    <tr><td>Sgo. del Estero</td></tr>
</table>

`GET`[`apis.datos.gob.ar/georef/api/provincias?nombre=Sgo.%20del%20Estero`](http://apis.datos.gob.ar/georef/api/provincias?nombre=Sgo.%20del%20Estero)
```json
{
  "provincias": [
    {
      "fuente": "IGN",
      "id": "86",
      "centroide_lat": -27.782412,
      "centroide_lon": -63.252387,
      "nombre": "Santiago del Estero"
    }
  ]
}
```

Cuando un conjunto de datos tiene puntos de coordenadas dentro de Argentina, puede cruzarse con muchos datos más, relacionados a las unidades territoriales que lo contienen. Para esto hay que agregarlas a los datos originales.

<table>
    <tr><td>lat</td><td>lon</td></tr>
    <tr><td>-27.2741</td><td>-66.7529</td></tr>
    <tr><td>-34.603633</td><td>-58.3837587</td></tr>
</table>

`GET`[`apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529`](http://apis.datos.gob.ar/georef/api/ubicacion?lat=-27.2741&lon=-66.7529)
```json
{
    "ubicacion": {
        "departamento": {
            "id": "10035",
            "nombre": "Belén"
        },
        "fuente": "IGN",
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
