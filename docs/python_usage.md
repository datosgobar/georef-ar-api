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

*TODO versión bulk del método*

## Con `pandas`

### Consultar lista de referencia

Todas las consultas a la API en formato CSV, se pueden leer fácilmente a un `pandas.DataFrame`.

```python
import pandas as pd

provincias = pd.read_csv("http://apis.datos.gob.ar/georef/api/provincias?formato=csv")
```

```
    provincia_id                                   provincia_nombre
0             14                                            Córdoba
1             22                                              Chaco
2             26                                             Chubut
3              6                                       Buenos Aires
4             10                                          Catamarca
5             30                                         Entre Ríos
6             34                                            Formosa
7             42                                           La Pampa
8             62                                          Río Negro
9             70                                           San Juan
10            78                                         Santa Cruz
11            82                                           Santa Fe
12            94  Tierra del Fuego, Antártida e Islas del Atlánt...
13            38                                              Jujuy
14            54                                           Misiones
15             2                    Ciudad Autónoma de Buenos Aires
16            18                                         Corrientes
17            46                                           La Rioja
18            66                                              Salta
19            86                                Santiago del Estero
20            50                                            Mendoza
21            58                                            Neuquén
22            74                                           San Luis
23            90                                            Tucumán
```

## Con `data-cleaner`

*TODO regla de limpieza*
