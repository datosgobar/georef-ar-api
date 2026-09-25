---
title: "Usar en Python"
---

Estos ejemplos usan Python 3 con [`requests`](https://requests.readthedocs.io/) y `pandas`. Las salidas son reales, de consultas a la v2.1.

## Con `requests`

### Normalizar una entidad

```python
import requests

API_BASE_URL = "https://apis.datos.gob.ar/georef/api/v2.1/"

def get_similar(endpoint, nombre, **kwargs):
    kwargs["nombre"] = nombre
    resp = requests.get(API_BASE_URL + endpoint, params=kwargs)
    resp.raise_for_status()
    # la clave de la respuesta usa guion bajo: gobiernos-locales -> gobiernos_locales
    return resp.json()[endpoint.replace("-", "_")]

provincias = get_similar("provincias", "San Juan")
```

```python
[{'centroide': {'lat': -30.865660702, 'lon': -68.888159707},
  'id': '70',
  'nombre': 'San Juan'}]
```

### Normalizar varias entidades

```python
def get_similar_bulk(endpoint, nombres):
    """Normaliza una lista de nombres con una consulta por lotes."""
    key = endpoint.replace("-", "_")
    data = {key: [{"nombre": nombre, "max": 1} for nombre in nombres]}
    resp = requests.post(API_BASE_URL + endpoint, json=data)
    resp.raise_for_status()

    # "resultado más probable" o {} cuando no hay resultados
    return [r[key][0] if r[key] else {} for r in resp.json()["resultados"]]

provincias = get_similar_bulk("provincias", ["pxa", "sant fe"])
```

```python
[{},
 {'centroide': {'lat': -30.708822709, 'lon': -60.950687277},
  'id': '82',
  'nombre': 'Santa Fe'}]
```

### Enriquecer coordenadas con las unidades territoriales que las contienen

```python
def get_territorial_units(ubicaciones):
    """Pide las unidades territoriales que contienen cada punto de una lista."""
    data = {
        "ubicaciones": [
            {"lat": u["lat"], "lon": u["lon"], "aplanar": True}
            for u in ubicaciones
        ]
    }
    resp = requests.post(API_BASE_URL + "ubicacion", json=data)
    resp.raise_for_status()
    return [r["ubicacion"] for r in resp.json()["resultados"]]

ubicaciones = get_territorial_units([
    {"lat": -32.9477132, "lon": -60.6304658},
    {"lat": -34.6037389, "lon": -58.3815704},
])
```

```python
[{'departamento_id': '82084',
  'departamento_nombre': 'Rosario',
  'gobierno_local_id': '820210',
  'gobierno_local_nombre': 'Rosario',
  'lat': -32.9477132,
  'lon': -60.6304658,
  'provincia_id': '82',
  'provincia_nombre': 'Santa Fe'},
 {'departamento_id': '02007',
  'departamento_nombre': 'Comuna 1',
  'gobierno_local_id': '022007',
  'gobierno_local_nombre': 'Comuna 1',
  'lat': -34.6037389,
  'lon': -58.3815704,
  'provincia_id': '02',
  'provincia_nombre': 'Ciudad Autónoma de Buenos Aires'}]
```

Cada pedido `POST` acepta hasta 1000 ubicaciones. Si tenés más, partí la lista en tandas.

## Con `pandas`

### Consultar listas de referencia

Cualquier consulta en formato CSV se puede leer directo en un `pandas.DataFrame`. Usá `dtype=str` para no perder los ceros a la izquierda de los IDs.

```python
import pandas as pd

provincias = pd.read_csv(API_BASE_URL + "provincias?formato=csv", dtype=str)
```

```
provincia_id                provincia_nombre provincia_centroide_lat provincia_centroide_lon
          02 Ciudad Autónoma de Buenos Aires           -34.614442065           -58.445876325
          58                         Neuquén           -38.641982863           -70.119897224
          74                        San Luis           -33.761103538           -66.025231271
          82                        Santa Fe           -30.708822709           -60.950687277
          46                        La Rioja           -29.684937278           -67.181757581
```

(Se muestran las primeras 5 de 24 filas.)

### Enriquecer coordenadas

```python
def add_territorial_units(df, column_lat, column_lon):
    """Agrega a un DataFrame las unidades territoriales que contienen sus coordenadas."""

    # coordenadas únicas (sin repetir)
    coordinates = df[[column_lon, column_lat]].rename(
        columns={column_lon: "lon", column_lat: "lat"}
    ).drop_duplicates().to_dict("records")

    # unidades territoriales de cada coordenada
    ubicaciones = pd.DataFrame(get_territorial_units(coordinates))

    # se agregan al DataFrame original
    df_with_territorial_units = df.merge(
        ubicaciones, "left",
        left_on=[column_lon, column_lat],
        right_on=["lon", "lat"]
    )

    # se quitan las columnas de coordenadas repetidas
    return df_with_territorial_units.drop(["lon", "lat"], axis=1)

df = pd.DataFrame({
    "nombre": ["Obelisco", "Monumento a la Bandera"],
    "latitud": [-34.6037389, -32.9477132],
    "longitud": [-58.3815704, -60.6304658],
})

df_with_territorial_units = add_territorial_units(df, "latitud", "longitud")
```

```
                nombre    latitud   longitud departamento_id departamento_nombre gobierno_local_id gobierno_local_nombre provincia_id                provincia_nombre
              Obelisco -34.603739 -58.381570           02007            Comuna 1            022007              Comuna 1           02 Ciudad Autónoma de Buenos Aires
Monumento a la Bandera -32.947713 -60.630466           82084             Rosario            820210               Rosario           82                        Santa Fe
```
