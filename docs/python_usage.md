# Usar en python

## Con `requests`

### Normalizar una entidad

```python
import requests
import urllib

API_BASE_URL = "http://apis.datos.gob.ar/georef/api/"

def get_similar(endpoint, nombre, **kwargs):
    kwargs["nombre"] = nombre
    url = "{}{}?{}".format(API_BASE_URL, endpoint, urllib.urlencode(kwargs))
    return requests.get(url).json()[endpoint]

provincias = get_similar("provincias", "San Juan")
```

```json
[{
    u'centroide_lat': -30.865368,
    u'centroide_lon': -68.889491,
    u'fuente': u'IGN',
    u'id': u'70',
    u'nombre': u'San Juan'
}]
```

### Normalizar varias entidades

```python
def get_similar_bulk(endpoint, nombres):
    data = { endpoint: [
        {"nombre": nombre, "max": 1} for nombre in nombres
    ]}
    url = API_BASE_URL + endpoint
    results = requests.post(url, json=data).json()

    # convierte a una lista de "resultado más probable" o "vacío" cuando no hay
    parsed_results = [
        single_result[endpoint][0] if single_result[endpoint] else {}
        for single_result in results["resultados"]
    ]

    return parsed_results

provincias = get_similar_bulk("provincias", ["pxa", "sant fe"])
```

```json
[
    {},
    {
        u'centroide_lat': -30.706927,
        u'centroide_lon': -60.949837,
        u'fuente': u'IGN',
        u'id': u'82',
        u'nombre': u'Santa Fe'
    }
]
```

## Con `pandas`

### Consultar lista de referencia

Todas las consultas a la API en formato CSV, se pueden leer fácilmente a un `pandas.DataFrame`.

```python
import pandas as pd

provincias = pd.read_csv("http://apis.datos.gob.ar/georef/api/provincias?formato=csv")
```

```
provincia_id                                   provincia_nombre
          14                                            Córdoba
          22                                              Chaco
          26                                             Chubut
           6                                       Buenos Aires
          10                                          Catamarca
          30                                         Entre Ríos
          34                                            Formosa
          42                                           La Pampa
          62                                          Río Negro
          70                                           San Juan
          78                                         Santa Cruz
          82                                           Santa Fe
          94  Tierra del Fuego, Antártida e Islas del Atlánt...
          38                                              Jujuy
          54                                           Misiones
           2                    Ciudad Autónoma de Buenos Aires
          18                                         Corrientes
          46                                           La Rioja
          66                                              Salta
          86                                Santiago del Estero
          50                                            Mendoza
          58                                            Neuquén
          74                                           San Luis
          90                                            Tucumán
```

### Enriquecer datos con coordenadas






## Con `data-cleaner`

*TODO regla de limpieza*
