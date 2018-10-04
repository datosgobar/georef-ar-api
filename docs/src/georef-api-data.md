# Modelo de datos para Georef API

Los archivos de datos de Georef consisten de cinco (5) archivos en formato JSON, los cuales contienen provincias, departamentos, municipios, localidades y calles.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [ETL](#etl)
- [Fuentes](#fuentes)
    - [Unidades Territoriales](#unidades-territoriales)
    - [BAHRA](#bahra)
    - [Vías de Circulación](#vias-de-circulacion)
- [Archivos](#archivos)
    - [Provincias](#provincias)
    - [Departamentos](#departamentos)
    - [Municipios](#municipios)
    - [Localidades](#localidades)
    - [Calles](#calles)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## ETL
Los datos utilizados por Georef API son obtenidos a través de un proceso de ETL. El código del mismo se encuentra en el repositorio GitHub [georef-ar-etl](https://github.com/datosgobar/georef-ar-etl), así también como su [guía de instalación y uso](https://github.com/datosgobar/georef-ar-etl/blob/master/docs/install.md).

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

## Archivos
A continuación se detallan, a través de ejemplos, los esquemas de los archivos para las entidades utilizadas. Notar que el campo `version` se utiliza al momento de indexar para determinar si los datos son compatibles con la versión de la API siendo utilizada; la versión detallada en este documento es la `5.0.0`.

### Provincias
El archivo de datos de provincias debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "5.0.0", // Versión de archivo
	"fuente": "IGN", // Fuente de los datos
	"datos": [ // Lista de entidades
		{
			"id": "90", // ID de provincia
			"nombre": "Tucumán", // Nombre de provincia
			"centroide": {
				"lat": -26.9478, // Latitud de centroide
				"lon": -65.36475 // Longitud de centroide
			},
			"geometria": {
				"type": "mutlipolygon", // Tipo de geometría
				"coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
			}
		},
		{ ... },
	]
}
```

### Departamentos
El archivo de datos de departamentos debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "5.0.0", // Versión de archivo
	"fuente": "IGN", // Fuente de los datos
	"datos": [ // Lista de entidades
		{
			"id": "06427", // ID del departamento
			"nombre": "La Matanza", // Nombre del departamento
			"centroide": {
				"lat": -34.770165, // Latitud de centroide
				"lon": -58.625449  // Longitud de centroide
			},
			"geometria": {
				"type": "mutlipolygon", // Tipo de geometría
				"coordinates": [[[[-58.4549, -34.5351], [-58.4545, -34.5353], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
			},
			"provincia": { // Provincia que contiene al departamento
				"id": "06",
				"nombre": "Buenos Aires"
			}
		},
		{ ... },
	]
}
```

### Municipios
El archivo de datos de municipios debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "5.0.0", // Versión de archivo
	"fuente": "IGN", // Fuente de los datos
	"datos": [ // Lista de entidades
		{
			"id": "060105", // ID del municipio
			"nombre": "Bolívar", // Nombre del municipio
			"centroide": {
				"lat": -36.298222, // Latitud de centroide
				"lon": -61.149648  // Longitud de centroide
			},
			"geometria": {
				"type": "mutlipolygon", // Tipo de geometría
				"coordinates": [[[[-58.4453, -34.4324], [-58.6463, -34.6841], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
			},
			"provincia": {  // Provincia que contiene al municipio
				"id": "06",
				"nombre": "Buenos Aires"
			}
		},
		{ ... },
	]
}
```

### Localidades
El archivo de datos de localidades debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "5.0.0", // Versión de archivo
	"fuente": "BAHRA", // Fuente de los datos
	"datos": [ // Lista de entidades
		{
			"id": "06189080000", // ID del asentamiento
			"nombre": "San Roman", // Nombre del asentamiento
			"tipo": "Localidad simple (LS)", // Tipo de asentamiento BAHRA
			"centroide": {
				"lat": -38.741555, // Latitud de centroide
				"lon": -61.537720  // Longitud de centroide
			},
			"geometria": {
				"type": "multipoint", // Tipo de geometría
				"coordinates": [[-61.5377, -38.7415], ...] // Listado de coordenadas (formato WKT) del MultiPoint
			},
			"municipio": { // Municipio que contiene al asentamiento
				"id": "060189", // Puede ser null
				"nombre": "Coronel Dorrego" // Puede ser null
			},
			"departamento": { // Departamento que contiene al asentamiento
				"id": "06070",
				"nombre": "Baradero"
			},
			"provincia": {  // Provincia que contiene al asentamiento
				"id": "06",
				"nombre": "Buenos Aires"
			}
		},
		{ ... },
	]
}
```

### Calles
El archivo de datos de calles debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Timestamp de creación
	"fecha_creacion": "2018-07-24 12:29:49.813835+00:00", // Fecha de creación
	"version": "5.0.0", // Versión de archivo
	"fuente": "INDEC", // Fuente de los datos
	"datos": [ // Lista de vías de circulación
		{
			"nomenclatura": "LARREA, Comuna 3, Ciudad Autónoma de Buenos Aires", // Nomenclatura: 'nombre, departamento, provincia'
			"id": "0202101007345", // ID de la vía de circulación
			"nombre": "LARREA", // Nombre de vía de circulación
			"tipo": "CALLE", // Tipo de vía de circulación
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
			"geometria": "0105000020E61000...", // Geometría MultiLineString en formato WKB, representación hexadecimal
			"departamento": { // Departamento
				"nombre": "Comuna 3",
				"id": "02021"
			},
			"provincia": { // Provincia
				"nombre": "Ciudad Autónoma de Buenos Aires",
				"id": "02"
			}
		},
		{ ... },
	]
}
```
