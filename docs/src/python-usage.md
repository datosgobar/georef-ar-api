# Usar en Python

## Con `requests`

### Normalizar una entidad

```python
import requests
import urllib

API_BASE_URL = "https://apis.datos.gob.ar/georef/api/"

def get_similar(endpoint, nombre, **kwargs):
    kwargs["nombre"] = nombre
    url = "{}{}?{}".format(API_BASE_URL, endpoint, urllib.urlencode(kwargs))
    return requests.get(url).json()[endpoint]

provincias = get_similar("provincias", "San Juan")
```

```python
[{
    u'centroide': {
        u'lat': -30.865368,
        u'lon': -68.889491
    },
    u'id': u'70',
    u'nombre': u'San Juan'
}]
```

### Normalizar varias entidades

```python
def get_similar_bulk(endpoint, nombres):
    """Normaliza una lista de nombres de alguna de las entidades geográficas."""

    # realiza consulta a la API
    data = {
        endpoint: [
            {"nombre": nombre, "max": 1} for nombre in nombres
    ]}
    url = API_BASE_URL + endpoint
    results = requests.post(
        url, json=data, headers={"Content-Type": "application/json"}
    ).json()

    # convierte a una lista de "resultado más probable" o "vacío" cuando no hay
    parsed_results = [
        single_result[endpoint][0] if single_result[endpoint] else {}
        for single_result in results["resultados"]
    ]

    return parsed_results

provincias = get_similar_bulk("provincias", ["pxa", "sant fe"])
```

```python
[
    {},
    {
        u'centroide': {
            u'lat': -30.706927,
            u'lon': -60.949837
        },
        u'id': u'82',
        u'nombre': u'Santa Fe'
    }
]
```

### Enriquecer coordenadas con las unidades territoriales que las contienen

```python
def get_territorial_units(ubicaciones):
    """Pide las unidades territoriales que contienen a c/punto de una lista de coordenadas."""

    # realiza consulta a la API
    endpoint = "ubicacion"
    data = {
        "ubicaciones": [
            {"lat": ubicacion["lat"], "lon": ubicacion["lon"], "aplanar": True}
            for ubicacion in ubicaciones
    ]}
    url = API_BASE_URL + endpoint

    results = requests.post(
        url, json=data, headers={"Content-Type": "application/json"}
    ).json()

    # convierte a una lista de "resultado más probable" o "vacío" cuando no hay
    parsed_results = [
        single_result[endpoint] if single_result[endpoint] else {}
        for single_result in results["resultados"]
    ]

    return parsed_results

ubicaciones = get_territorial_units([
    {"lat": -32.9477132, "lon": -60.6304658},
    {"lat": -34.6037389, "lon": -58.3815704}
])
```

```python
[
    {
        u'departamento_id': u'30105',
        u'departamento_nombre': u'Victoria',
        u'lat': -32.9477132,
        u'lon': -60.6304658,
        u'municipio_id': u'82210',
        u'municipio_nombre': u'Rosario',
        u'provincia_id': u'30',
        u'provincia_nombre': u'Entre Ríos'
    },
    {
        u'departamento_id': u'02007',
        u'departamento_nombre': u'Comuna 1',
        u'lat': -34.6037389,
        u'lon': -58.3815704,
        u'municipio_id': None,
        u'municipio_nombre': None,
        u'provincia_id': u'02',
        u'provincia_nombre': u'Ciudad Autónoma de Buenos Aires'
    }
]
```

## Con `pandas`

### Consultar listas de referencia

Todas las consultas a la API en formato CSV, se pueden leer fácilmente a un `pandas.DataFrame`. De ahí se pueden tomar listas de referencia para distintas unidades territoriales.

```python
import pandas as pd

provincias = pd.read_csv("https://apis.datos.gob.ar/georef/api/provincias?formato=csv")
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

### Enriquecer coordenadas

```python
def add_territorial_units(df, column_lat, column_lon):
    """Agrega unidades territoriales que contienen coordenadas a un DataFrame.

    Args:
        df (pandas.DataFrame): Un DataFrame que tiene coordenadas.
        column_lat (str): Nombre de la columna que tiene latitud.
        column_lon (str): Nombre de la columna que tiene longitud.

    Returns:
        pandas.DataFrame: DataFrame original aumentado con unidades       territoriales que contienen a las coordenadas.
    """

    # toma una lista de coordenadas únicas (no repetidas)
    coordinates = df[[column_lon, column_lat]].rename(
        columns={column_lon: "lon", column_lat: "lat"}
    ).drop_duplicates().to_dict("records")

    # crea DataFrame de unidades territoriales que contienen a las coordenadas
    ubicaciones = pd.DataFrame(get_territorial_units(coordinates))

    # agrega las unidades territoriales al DataFrame original
    df_with_territorial_units = df.merge(
        ubicaciones, "left",
        left_on=[column_lon, column_lat],
        right_on=["lon", "lat"]
    )

    # elimina columnas de coordenadas repetidas, dejando las originales
    return df_with_territorial_units.drop(["lon", "lat"], axis=1)

# descarga un CSV con coordenadas de aeropuertos
df = pd.read_csv("https://servicios.transporte.gob.ar/gobierno_abierto/descargar.php?t=aeropuertos&d=detalle", sep=";")

# Agrega unidades territoriales que contienen coordenadas a un DataFrame
df_with_territorial_units = add_territorial_units(df, "longitud", "latitud")
```

```
   tipo                       denominacion   latitud  longitud   elev  \
Aeródromo       CORONEL BOGADO/AGROSERVICIOS -60.57066 -33.27226   44.0
Aeródromo                       GENERAL ACHA -64.61351 -37.40164  277.0
Aeródromo            ARRECIFES/LA CURA MALAL -60.14170 -34.07574   37.0
Aeródromo                     PUERTO DESEADO -65.90410 -47.73511   82.0
Aeródromo  BANDERA/AGROSERVICIOS DOÑA TERESA -62.26462 -28.85541   75.0

departamento_id departamento_nombre municipio_id municipio_nombre  \
          82084             Rosario       823393   Coronel Bogado
          42154             Utracán       420133     General Acha
          06077           Arrecifes       060077        Arrecifes
          78014             Deseado         None             None
          86077     General Taboada         None             None

provincia_id     provincia_nombre
          82             Santa Fe
          42             La Pampa
          06         Buenos Aires
          78           Santa Cruz
          86  Santiago del Estero
```

<!-- ## Con `data-cleaner` -->
