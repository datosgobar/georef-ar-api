# Modelo de datos para Georef

**Versión**: 12.0.0

El fin del proceso ETL de Georef es producir archivos con datos de entidades geográficas. El ETL genera varios archivos: unos de ellos son utilizados para ser indexados por la API, y otros sirven para facilitar a usuarios de la API descargarse la totalidad de los datos en distintos formatos.

Los archivos generados para ser indexados en la API tienen formato [NDJSON](http://ndjson.org/). El formato NDJSON consiste en un archivo de texto donde cada línea (separadas por `\n`) es un objeto JSON válido. Los archivos generados son:

- `provincias.ndjson`
- `departamentos.ndjson`
- `municipios.ndjson`
- `localidades.ndjson`
- `calles.ndjson`
- `intersecciones.ndjson`
- `cuadras.ndjson`
- `localidades-censales.ndjson`
- `asentamientos.ndjson`

Los archivos generados para la descarga de datos para usuarios de la API tienen tres formatos: JSON, GeoJSON y CSV. La tabla completa de los archivos generados se encuentra detallada en la sección de [instalación y ejecución del ETL](etl-install.md#3-resultados). **Se recomienda el uso de los archivos NDJSON si se desea procesar todos los datos de entidades geográficas.** Esto se debe a que el formato se presta a ser leído por partes (líneas), lo cual facilita el procesamiento de los archivos de gran tamaño. Notar que el único formato que incluye las geometrías de las entidades geográficas es NDJSON.

## Fuentes
Los orígenes de los datos procesados en el ETL son:

### Unidades Territoriales
- Recursos: `/provincias`, `/departamentos`, `/municipios`, `/ubicacion`
- Fuente: **Instituto Geográfico Nacional (IGN)**
- Enlace: [Datos Abiertos - Unidades Territoriales](http://datos.gob.ar/dataset/ign-unidades-territoriales)

### BAHRA
- Recursos: `/localidades`
- Fuente: **Base de Asentamientos Humanos de la República Argentina (BAHRA)**
- Enlace: [BAHRA - Descargas](http://www.bahra.gob.ar/)

### Vías de Circulación
- Recursos: `/calles`, `/direcciones`
- Fuente: **Instituto Nacional de Estadística y Censos de la República Argentina (INDEC)**
- Enlace: [Portal de geoservicios de INDEC](https://geoservicios.indec.gov.ar/nomenclador-vias-de-circulacion/?contenido=descargas)

### Cuadras
- Recursos: `/calles`, `/direcciones`
- Fuente: **Instituto Nacional de Estadística y Censos de la República Argentina (INDEC)**
- Enlace: [GeoServer INDEC](https://geoservicios.indec.gov.ar/geoserver)

### Localidades Censales
- Recursos: `/localidad-censales`
- Fuente: **Instituto Nacional de Estadística y Censos de la República Argentina (INDEC)**
- Enlace: [Unidades Geoestadísticas - Cartografía y códigos geográficos del Sistema Estadístico Nacional](https://www.indec.gov.ar/codgeo.asp).

## Descarga de los archivos
Todos los archivos mencionados anteriormente pueden ser descargados desde el portal de descargas `infra.datos.gob.ar`. Los enlaces están catalogados en el portal de datos abiertos, bajo la [distribución del servicio de normalización de datos geográficos](https://datos.gob.ar/dataset/modernizacion-servicio-normalizacion-datos-geograficos).

## Archivos
A continuación se detallan, a través de ejemplos, los esquemas de los archivos NDJSON para todas las entidades geográficas.

La primera línea de cada archivo contiene los metadatos del archivo. La estructura de los metadatos es la siguiente:
```json
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "X.0.0", // Versión de archivo
	"cantidad": 100 // Cantidad de entidades
}
```

Recordar que todo el objeto JSON aparece serializado en la primera línea del archivo, de la siguiente forma:

```json
{"timestamp": "1532435389","fecha_creacion": "2018-07-24 12:29:49.813835+00:00","version":"X.0.0","cantidad": 100}
```


Luego, el resto de las líneas del archivo contienen las entidades en formato JSON, una por línea. Todas las geometrías incluidas en los archivos utilizan el sistema de coordenadas **WGS84** (**EPSG 4326**).

### Provincias (`provincias.ndjson`)
Cada línea del archivo de datos de provincias tiene la siguiente estructura:
```
{
	"id": "90", // ID de provincia
	"nombre": "Tucumán", // Nombre de provincia,
	"nombre_completo": "Provincia de Tucumán", // Nombre completo
	"iso_id": "AR-T", // Identificador ISO 3166-2
	"iso_nombre": "Tucumán", // Nombre ISO
	"categoria": "Provincia", // Tipo de entidad
	"centroide": {
		"lat": -26.9478, // Latitud de centroide
		"lon": -65.36475 // Longitud de centroide
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiPolygon",
		"coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]]
	},
	"fuente": "IGN" // Fuente del dato
}
```

### Departamentos (`departamentos.ndjson`)
Cada línea del archivo de datos de departamentos tiene la siguiente estructura:
```
{
	"id": "06427", // ID del departamento
	"nombre": "La Matanza", // Nombre del departamento
	"nombre_completo": "Partido de la Matanza", // Nombre completo
	"categoria": "Partido", // Tipo de entidad
	"centroide": {
		"lat": -34.770165, // Latitud de centroide
		"lon": -58.625449  // Longitud de centroide
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiPolygon",
		"coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]]
	},
	"provincia": { // Provincia que contiene al departamento
		"id": "06",
		"nombre": "Buenos Aires",
		"interseccion": "0.0412936" // Porcentaje del área de la provincia que ocupa el depto.
	},
	"fuente": "ARBA - Gerencia de Servicios Catastrales" // Fuente del dato
}
```

### Municipios (`municipios.ndjson`)
Cada línea del archivo de datos de municipios tiene la siguiente estructura:
```
{
	"id": "060105", // ID del municipio
	"nombre": "Bolívar", // Nombre del municipio
	"nombre_completo": "Municipio Bolívar", // Nombre completo
	"categoria": "Municipio", // Tipo de entidad
	"centroide": {
		"lat": -36.298222, // Latitud de centroide
		"lon": -61.149648  // Longitud de centroide
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiPolygon",
		"coordinates": [[[[-58.4453, -34.4324], [-58.6463, -34.6841], ...]]]
	},
	"provincia": {  // Provincia que contiene al municipio
		"id": "06",
		"nombre": "Buenos Aires",
		"interseccion": "0.0100845" // Porcentaje del área de la provincia que ocupa el municipio
	},
	"fuente": "ARBA - Gerencia de Servicios Catastrales" // Fuente del dato
}
```

### Localidades (`localidades.ndjson`)
Cada línea del archivo de datos de localidades tiene la siguiente estructura:
```
{
	"id": "06189080000", // ID de la localidad
	"nombre": "San Roman", // Nombre de la localidad
	"categoria": "Localidad simple (LS)", // Tipo de asentamiento BAHRA
	"centroide": {
		"lat": -38.741555, // Latitud de centroide
		"lon": -61.537720  // Longitud de centroide
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiPoint",
		"coordinates": [[-61.5377, -38.7415], ...]
	},
	"municipio": { // Municipio que contiene a la localidad
		"id": "060189", // Puede ser nulo
		"nombre": "Coronel Dorrego" // Puede ser nulo
	},
	"departamento": { // Departamento que contiene a la localidad
		"id": "06189",
		"nombre": "Coronel Dorrego"
	},
	"provincia": {  // Provincia que contiene a la localidad
		"id": "06",
		"nombre": "Buenos Aires"
	},
	"fuente": "INDEC" // Fuente del dato
}
```

### Calles (`calles.ndjson`)
Cada línea del archivo de datos de calles tiene la siguiente estructura:
```
{
	"id": "0202101007345", // ID de la vía de circulación
	"nombre": "LARREA", // Nombre de vía de circulación
	"categoria": "CALLE", // Tipo de vía de circulación
	"altura": {
		"inicio": {
			"derecha": 1, // Número inicial de altura (lado derecho)
			"izquierda": 2, // Número inicial de altura (lado izquierdo)
		},
		"fin": {
			"derecha": 799, // Número final de altura (lado derecho)
			"izquierda": 800, // Número final de altura (lado izquierdo)
		}
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiLineString",
		"coordinates": [[[-58.52815846522327, -34.611800397637424], ...]]
	},
	"departamento": { // Departamento
		"nombre": "Comuna 3",
		"id": "02021"
	},
	"provincia": { // Provincia
		"nombre": "Ciudad Autónoma de Buenos Aires",
		"id": "02"
	},
	"fuente": "INDEC" // Fuente del dato
}
```

### Intersecciones de Calles (`intersecciones.ndjson`)
El archivo de datos de intersecciones contiene todas las intersecciones existentes entre calles. Dadas dos calles, se listan todas las intersecciones que las mismas comparten (una o más). El ID de cada intersección está compuesto de tres partes: el ID de la primera calle, el ID de la segunda, y el número de intersección entre las dos calles (comenzando desde `01`). **No se repiten intersecciones**: es decir, dadas las calles con ID X y ID Z, solo están presentes las intersecciones X-Z-N o las Z-X-N, pero no ambos grupos. Cada línea del archivo de datos de intersecciones tiene la siguiente estructura:
```
{
	// ID de la calle A, ID de la calle B, número de intersección (dos dígitos)
	"id": "0207001002300-0207001007975-01",
	"calle_a": {
		"id": "0207001002300", // ID de la calle A
		"nombre": "BOSTON", // Nombre de la calle A
		"departamento": { // Departamento de la calle A
			"id": "02070",
			"nombre": "Comuna 10"
		},
		"provincia": { // Provincia de la calle A
			"id": "02",
			"nombre": "Ciudad Autónoma de Buenos Aires"
		},
		"categoria": "CALLE", // Tipo de la calle A
		"fuente": "INDEC" // Fuente del dato
	},
	"calle_b": {
		"id": "0207001007975", // ID de la calle B
		"nombre": "MARCOS SASTRE", // Nombre de la calle B
		"departamento": { // Departamento de la calle B
			"id": "02070",
			"nombre": "Comuna 10"
		},
		"provincia": { // Provincia de la calle B
			"id": "02",
			"nombre": "Ciudad Autónoma de Buenos Aires"
		},
		"categoria": "CALLE", // Tipo de la calle B
		"fuente": "INDEC" // Fuente del dato
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "Point",
		"coordinates": [
			-58.5077676091915,
			-34.6150993860767
		]
	}
}
```

### Cuadras (`cuadras.ndjson`)
Cada línea del archivo de datos de cuadras tiene la siguiente estructura:
```
{
    "id": "020700100230012345", // ID de la cuadra
	"calle": {
		"id": "0207001002300", // ID de la calle
		"nombre": "BOSTON", // Nombre de la calle
		"departamento": { // Departamento de la calle
			"id": "02070",
			"nombre": "Comuna 10"
		},
		"provincia": { // Provincia de la calle
			"id": "02",
			"nombre": "Ciudad Autónoma de Buenos Aires"
		},
		"categoria": "CALLE", // Tipo de la calle
		"fuente": "INDEC" // Fuente del dato
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiLineString",
		"coordinates": [[[-58.52815846522327, -34.611800397637424], ...]]
	}
}
```

### Localidades Censales (`localidades-censales.ndjson`)
Cada línea del archivo de datos de localidades censales tiene la siguiente estructura:
```
{
    "id": "06441030", // ID de la localidad censal
    "nombre": "La Plata", // Nombre de la localidad censal
    "fuente": "INDEC", // Fuente del dato
    "provincia": { // Provincia de la localidad censal
        "id": "06",
        "nombre": "Buenos Aires"
    },
    "departamento": { // Departamento de la localidad censal
        "id": "06441",
        "nombre": "La Plata"
    },
    "municipio": { // Municipio que contiene a la localidad censal
        "id": "060441",
        "nombre": "La Plata"
    },
    "categoria": "Componente de localidad compuesta (LC)", // Tipo de localidad del censo
    "funcion": "CAPITAL_PROVINCIA", // Función administrativa, puede ser null
    "centroide": {
        "lon": -57.9543916496992, // Longitud del centroide
        "lat": -34.9220666561801 // Latitud del centroide
    },
    "geometria": { // Geometría en formato GeoJSON
        "type": "Point",
        "coordinates": [
            -57.9543916496992,
            -34.9220666561801
        ]
    }
}
```

### Asentamientos (`asentamientos.ndjson`)
Cada línea del archivo de datos de asentamientos tiene la siguiente estructura (idéntica a la de localidades):
```
{
	"id": "06189080000", // ID de la localidad
	"nombre": "San Roman", // Nombre de la localidad
	"categoria": "Localidad simple (LS)", // Tipo de asentamiento BAHRA
	"centroide": {
		"lat": -38.741555, // Latitud de centroide
		"lon": -61.537720  // Longitud de centroide
	},
	"geometria": { // Geometría en formato GeoJSON
		"type": "MultiPoint",
		"coordinates": [[-61.5377, -38.7415], ...]
	},
	"municipio": { // Municipio que contiene a la localidad
		"id": "060189", // Puede ser nulo
		"nombre": "Coronel Dorrego" // Puede ser nulo
	},
	"departamento": { // Departamento que contiene a la localidad
		"id": "06189",
		"nombre": "Coronel Dorrego"
	},
	"provincia": {  // Provincia que contiene a la localidad
		"id": "06",
		"nombre": "Buenos Aires"
	},
	"fuente": "INDEC" // Fuente del dato
}
```

## Procesamiento
Para procesar los archivos de datos con Python, se puede utilizar el módulo estándar `json`. Se recomienda iterar sobre el objeto devuelto por `open()` para evitar cargar todo el archivo en memoria a la vez:

```python
import json

with open('calles.ndjson') as f:
	# Leer la línea de metadatos
	metadata = json.loads(next(f))

	# Leer cada línea y parsear el JSON
	for line in f:
		street = json.loads(line)
		# La variable street ahora contiene un dict con los datos de la calle
```
