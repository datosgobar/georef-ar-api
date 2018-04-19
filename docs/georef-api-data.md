# Modelo de datos para Georef API

Los datos utilizados por la API están separados en dos grupos: **entidades** y **vías de circulación**. El grupo de entidades está compuesto por cinco (5) archivos `.json`, los cuales contienen provincias, departamentos, municipios, localidades y asentamientos. Por el otro lado, el grupo de las vías está compuesto por veinticuatro (24) archivos `.json`, los cuales detallan las vías de circulación de cada provincia y la Ciudad Autónoma de Buenos Aires (CABA).

## Fuentes
Los datos utilizados por Georef API fueron obtenidos a través de un proceso de ETL. Los orígenes de los datos procesados son:
- Entidades: [Portal de datos abiertos](http://datos.gob.ar/dataset/unidades-territoriales)
- Vías de circulación: [Portal de geoservicios de INDEC](https://geoservicios.indec.gov.ar/nomenclador-vias-de-circulacion/?contenido=descargas)

## Entidades
A continuación se detallan, a través de ejemplos, los esquemas de los archivos `.json` para las entidades:

### Provincias
El archivo de datos de provincias debe llamarse `provincias.json` y tener formato JSON. El esquema de datos debe ser el siguiente:
```
[
    {
        "id": "02", // ID de provincia
        "nombre": "CIUDAD AUTÓNOMA DE BUENOS AIRES", // Nombre de provincia
        "lat": "-34.614493", // Latitud de centroide
        "lon": "-58.445856", // Longitud de centroide
        "geometry": {
            "type": "mutlipolygon", // Tipo de geometría
            "coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
        }
    },
    { ... },
]
```

### Departamentos
El archivo de datos de departamentos debe llamarse `departamentos.json` y tener formato JSON. El esquema de datos debe ser el siguiente:
```
[
    {
        "id": "06427", // ID del departamento
        "nombre": "LA MATANZA", // Nombre del departamento
        "lat": "-34.770165", // Latitud de centroide
        "lon": "-58.625449", // Longitud de centroide
        "geometry": {
            "type": "mutlipolygon", // Tipo de geometría
            "coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
        },
        "provincia": { // Provincia que contiene al departamento
            "id": "06",
            "nombre": "BUENOS AIRES"
        }
    },
    { ... },
]
```

### Municipios
El archivo de datos de municipios debe llamarse `municipios.json` y tener formato JSON. El esquema de datos debe ser el siguiente:
```
[
    {
        "id": "060105", // ID del municipio
        "nombre": "BOLÍVAR", // Nombre del municipio
        "lat": "-36.298222", // Latitud de centroide
        "lon": "-61.149648", // Longitud de centroide
        "geometry": {
            "type": "mutlipolygon", // Tipo de geometría
            "coordinates": [[[[-58.4453, -34.4324], [-58.6463, -34.6841], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
        },
        "departamento": { // Departamento que contiene al municipio
            "id": "06105",
            "nombre": "BOLÍVAR"
        },
        "provincia": {  // Provincia que contiene al municipio
            "id": "06",
            "nombre": "BUENOS AIRES"
        }
    },
    { ... },
]
```

### Localidades
El archivo de datos de localidades debe llamarse `localidades.json` y tener formato JSON. El esquema de datos debe ser el siguiente:
```
[
    {
        "id": "06070040", // ID de la localidad
        "nombre": "VILLA ALSINA", // Nombre de la localidad
        "departamento": { // Departamento que contiene a la localidad
            "id": "06070",
            "nombre": "BARADERO"
        },
        "provincia": {  // Provincia que contiene a la localidad
            "id": "06",
            "nombre": "BUENOS AIRES"
        }
    },
    { ... },
]
```

### Asentamientos
El archivo de datos de asentamientos debe llamarse `asentamientos.json` y tener formato JSON. El esquema de datos debe ser el siguiente:
```
[
    {
        "id": "06189080000", // ID del asentamiento
        "nombre": "SAN ROMAN", // Nombre del asentamiento
        "tipo": "Localidad simple (LS)", // Tipo de asentamiento BAHRA
        "lat": "-38.741555", // Latitud
        "lon": "-61.537720", // Longitd
        "geometry": {
            "type": "multipoint", // Tipo de geometría
            "coordinates": [[-61.5377, -38.7415], ...] // Listado de coordenadas (formato WKT) del MultiPoint
        },
        "municipio": { // Municipio que contiene al asentamiento
            "id": "060189", // Puede ser null
            "nombre": "CORONEL DORREGO" // Puede ser null
        },
        "departamento": { // Departamento que contiene al asentamiento
            "id": "06070",
            "nombre": "BARADERO"
        },
        "provincia": {  // Provincia que contiene al asentamiento
            "id": "06",
            "nombre": "BUENOS AIRES"
        }
    },
    { ... },
]
```

## Vías de Circulación
Cada archivo de vías de circulación debe llamarse `calles-XX.json`, donde `XX` es el código INDEC de dos dígitos de la provincia o CABA. El esquema de datos de cada archivo debe ser el siguiente:
```
[
    {
        "nomenclatura": "LARREA, CIUDAD AUTÓNOMA DE BUENOS AIRES, CIUDAD AUTÓNOMA DE BUENOS AIRES", // Nomenclatura: 'nombre, localidad, provincia'
        "id": "0202101007345", // ID de la vía de circulación
        "nombre": "LARREA", // Nombre de vía de circulación
        "tipo": "CALLE", // Tipo de vía de circulación
        "inicio_derecha": 1, // Número inicial de altura (lado derecho)
        "inicio_izquierda": 2, // Número inicial de altura (lado izquierdo)
        "fin_derecha": 799, // Número final de altura (lado derecho)
        "fin_izquierda": 800, // Número final de altura (lado izquierdo)
        "geometria": "0105000020E61000...", // Geometría MultiLineString en formato WKB, representación hexadecimal
        "codigo_postal": "C1030AAJ", // Código postal, puede ser null
        "localidad": "CIUDAD AUTÓNOMA DE BUENOS AIRES", // Localidad
        "departamento": "COMUNA 3", // Departamento
        "provincia": "CIUDAD AUTÓNOMA DE BUENOS AIRES" // Provincia
    },
    { ... },
]
```
