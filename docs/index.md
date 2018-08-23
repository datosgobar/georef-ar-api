# API del Servicio de Normalización de Datos Geográficos de Argentina

La API del Servicio de Normalización de Datos Geográficos, permite normalizar y codificar los nombres de unidades territoriales de la Argentina (provincias, departamentos, municipios y localidades) y de sus calles, así como ubicar coordenadas dentro de ellas.

---

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
            "nombre": "Santiago del Estero",
            "id": "86",
            "fuente": "IGN",
            "centroide": {
                "lat": -27.782412,
                "lon": -63.252387
            }
        }
    ]
}
```

---

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

---

Finalmente, se puede utilizar la API como punto de referencia al momento de crear datos que estén vinculados a datos geográficos. Por ejemplo, si se cuenta con un formulario en el que se debe mostrar a un usuario un listado de provincias, y luego un listado de municipios a partir de la provincia seleccionada, se podrían ejecutar las siguientes consultas:

Listar las provincias de la República Argentina:

`GET`[`apis.datos.gob.ar/georef/api/provincias?campos=id,nombre`](http://apis.datos.gob.ar/georef/api/provincias)
```json
{
    "provincias": [
        {
            "nombre": "Chaco",
            "id": "22",
            "fuente": "IGN"
        },
		{ ... } // 23 resultados omitidos
    ]
}
```

Asumiendo que el usuario selecciona **Chaco** (ID: **22**), se ejecutaría la siguiente consulta para obtener el listado de municipios:

`GET`[`apis.datos.gob.ar/georef/api/municipios?provincia=22&campos=id,nombre&max=100`](http://apis.datos.gob.ar/georef/api/municipios?provincia=22&campos=id,nombre&max=100)
```json
{
    "municipios": [
        {
            "nombre": "Makallé",
            "id": "220161",
            "fuente": "IGN"
        },
		{ ... } // 67 resultados omitidos
    ]
}
```

Notar que al ser datos que no son modificados regularmente, es posible retener copias de los mismos para ser reutilizados en el futuro.
