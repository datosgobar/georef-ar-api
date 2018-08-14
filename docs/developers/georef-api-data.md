# Modelo de datos para Georef API

Los archivos de datos de Georef consisten de cinco (5) archivos en formato JSON, los cuales contienen provincias, departamentos, municipios, asentamientos y vías de circulación (calles).

## Fuentes
Los datos utilizados por Georef API fueron obtenidos a través de un proceso de ETL. Los orígenes de los datos procesados son:
- Entidades: [Portal de datos abiertos](http://datos.gob.ar/dataset/unidades-territoriales)
- Vías de circulación: [Portal de geoservicios de INDEC](https://geoservicios.indec.gov.ar/nomenclador-vias-de-circulacion/?contenido=descargas)

## Archivos
A continuación se detallan, a través de ejemplos, los esquemas de los archivos para las entidades utilizadas. Notar que el campo `version` se utiliza al momento de indexar para determinar si los datos son compatibles con la versión de la API siendo utilizada.

### Provincias
El archivo de datos de provincias debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Fecha de creación de los datos,
	"version": "0.1.0", // Versión de archivo
	"entidades": [ // Lista de entidades
		{
			"id": "90", // ID de provincia
			"nombre": "Tucumán", // Nombre de provincia
			"lat": -26.9478, // Latitud de centroide
			"lon": -65.36475, // Longitud de centroide
			"geometry": {
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
	"timestamp": "1532435389", // Fecha de creación de los datos
	"version": "0.1.0", // Versión de archivo
	"entidades": [ // Lista de entidades
		{
			"id": "06427", // ID del departamento
			"nombre": "La Matanza", // Nombre del departamento
			"lat": -34.770165, // Latitud de centroide
			"lon": -58.625449, // Longitud de centroide
			"geometry": {
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
	"timestamp": "1532435389", // Fecha de creación de los datos
	"version": "0.1.0", // Versión de archivo
	"entidades": [ // Lista de entidades
		{
			"id": "060105", // ID del municipio
			"nombre": "Bolívar", // Nombre del municipio
			"lat": -36.298222, // Latitud de centroide
			"lon": -61.149648, // Longitud de centroide
			"geometry": {
				"type": "mutlipolygon", // Tipo de geometría
				"coordinates": [[[[-58.4453, -34.4324], [-58.6463, -34.6841], ...]]] // Listado de coordenadas (formato WKT) del MultiPolygon
			},
			"departamento": { // Departamento que contiene al municipio
				"id": "06105",
				"nombre": "Bolívar"
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

### Asentamientos
El archivo de datos de asentamientos debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Fecha de creación de los datos
	"version": "0.1.0", // Versión de archivo
	"entidades": [ // Lista de entidades
		{
			"id": "06189080000", // ID del asentamiento
			"nombre": "San Roman", // Nombre del asentamiento
			"tipo": "Localidad simple (LS)", // Tipo de asentamiento BAHRA
			"lat": -38.741555, // Latitud
			"lon": -61.537720, // Longitd
			"geometry": {
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

### Vías de Circulación
El archivo de datos de vías de circulación debe tener formato JSON. Su esquema de datos debe ser el siguiente:
```
{
	"timestamp": "1532435389", // Fecha de creación de los datos
	"version": "0.1.0", // Versión de archivo
	"vias": [ // Lista de vías de circulación
		{
			"nomenclatura": "LARREA, Comuna 3, Ciudad Autónoma de Buenos Aires", // Nomenclatura: 'nombre, departamento, provincia'
			"id": "0202101007345", // ID de la vía de circulación
			"nombre": "LARREA", // Nombre de vía de circulación
			"tipo": "CALLE", // Tipo de vía de circulación
			"inicio_derecha": 1, // Número inicial de altura (lado derecho)
			"inicio_izquierda": 2, // Número inicial de altura (lado izquierdo)
			"fin_derecha": 799, // Número final de altura (lado derecho)
			"fin_izquierda": 800, // Número final de altura (lado izquierdo)
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
