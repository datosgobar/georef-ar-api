# Georef API - Guía de instalación para entorno de desarrollo

## Dependencias

- [Elasticsearch >=6.2.0](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGIS 2.3](http://postgis.net/install/)

## Datos

En [este documento](georef-api-data.md) se detalla el modelo de datos utilizado por la API y las URLs donde se encuentran publicados.

## Instalación
### Base de datos

Crear una base de datos en PostgreSQL con la extensión PostGIS.

Ejemplo utilizando `georef_api` como nombre para la base de datos:

```plsql
-- Crear la base de datos:
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregar PostGIS a la base de datos creada:
CREATE EXTENSION postgis;
```

### Repositorio y dependencias

- Clonar el repositorio:

    `$ git clone https://github.com/datosgobar/georef-api.git`

	`$ cd georef-api`
    
- Crear un entorno virtual y activarlo:

    `$ python3 -m venv venv`
    
    `$ source venv/bin/activate`
 
- Instalar dependencias con `pip`:
    
    `(venv) $ pip3 install -r requirements.txt`

- Copiar el archivo de configuración:

    `(venv) $ cp config/georef.example.cfg config/georef.cfg`
    
- Completar el archivo `config/georef.cfg` con los valores apropiados.

### Elasticsearch

- Instalar el entorno de ejecución para Java:

    `$ sudo apt install default-jre`
  
- Descargar y descomprimir Elasticsearch:

    `$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.tar.gz`

    `$ tar -xzvf elasticsearch-6.2.0.tar.gz`

- Iniciar Elasticsearch:

    `$ cd directorio/a/elasticsearch/bin/ && ./elasticseach`
  
- Probar el servicio local:

    `$ curl -X GET 'http://localhost:9200'`
    
### Archivos de datos

- El archivo de configuración `config/georef.cfg` debe especificar una ruta local o una URL externa para cada archivo de datos JSON. Notar que los valores por defecto (en `georef.example.cfg`) utilizan el portal de descargas `infra.datos.gob.ar`, que siempre provee la última versión de los archivos JSON disponibles.

- Adicionalmente, se debe crear un archivo `georef_synonyms.txt`, en la ubicación del archivo de configuración de Elasticsearch (`$ES_HOME/config`). El archivo contiene la base de sinónimos utilizados al momento de indexar documentos. Su contenido puede ser vacío.

### Cargar las funciones SQL

- Cargar las funciones SQL necesarias para el funcionamiento de la API:

	`(venv) $ make load_sql`

### Crear los índices
    
- Generar índices de entidades y calles.

    `(venv) $ make index`
        
- Listar los índices creados, y otros datos adicionales:

    `(venv) $ make print_index_stats`
	
### Re-indexar datos

Si se modifican los archivos de datos JSON, es posible re-indexarlos sin borrar los índices ya existentes. Dependiendo del comportamiento que se desee, se debe tomar una opción:

- Si se desea actualizar los índices con los nuevos datos, solo si los datos entrantes son más recientes, se puede utilizar nuevamente:
  
    `(venv) $ make index`
    
- Si se desea forzar un re-indexado, es decir, si se desea indexar los datos nuevamente sin importar la fecha de creación, se debe utilizar la siguiente receta:

    `(venv) $ make index_forced`
	
  La receta `index_forced` intenta utilizar un archivo de respaldo guardado anteriormente si no pudo acceder a los archivos especificados en `config/georef.cfg`.

## Correr API 

- Correr `georef-api`, utilizando un servidor de prueba (no apto para producción):
    
    `(venv) $ make start_dev_server`

## Tests

- Tests unitarios (los servicios Elasticsearch y PostgreSQL deben estar activos y con los datos apropiados cargados):

    `(venv) $ make test_all`

