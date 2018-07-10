# Georef API - Guía de instalación para entorno de desarrollo

## Dependencias

- [Elasticsearch >=6.2.0](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGIS 2.3](http://postgis.net/install/)
- `wget`

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
    
    `(venv)$ pip3 install -r requirements.txt`

- Copiar las variables de entorno:

    `(venv)$ cp environment.example.sh environment.sh`
    
- Completar el archivo `environment.sh` con los datos correspondientes:

    ```bash
    export GEOREF_API_DB_HOST= # Dirección de la base de datos PostgreSQL
    export GEOREF_API_DB_NAME= # Nombre de la base de datos (por ejemplo, 'georef_api')
    export GEOREF_API_DB_USER= # Usuario de la base de datos
    export GEOREF_API_DB_PASS= # Contraseña del usuario de la base de datos
 
    export ENTIDADES_DATA_DIR= # /directorio/datos/de/entidades
    export VIAS_DATA_DIR= # /directorio/datos/de/vias
 
    export FLASK_APP=service/__init__.py
    export FLASK_DEBUG=1
    ```

- Cargar funciones en PostgreSQL:

    `(venv)$ python3 scripts/functions_load.py`
 
### Elasticsearch

- Instalar el entorno de ejecución para Java:

    `$ sudo apt install default-jre`
  
- Descargar y descomprimir Elasticsearch:

    `$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.tar.gz`

    `$ tar -xzvf elasticsearch-6.2.0.tar.gz`

- Levantar el servicio de Elasticsearch:

    `$ cd directorio/a/elasticsearch/bin/ && ./elasticseach`
  
- Probar el servicio:

    `$ curl -X GET 'http://localhost:9200'`
    
### Crear los índices

- Importar variables de entorno:
    
    `(venv)$ . environment.sh`
    
- Generar índices de entidades. Se debe contar con los archivos de datos para entidades mencionados al comienzo de la guía, y sus directorios deben estar en las variables de entorno (vía el archivo `environment.sh`).

    `(venv)$ make indexar_todos`
        
- Listar los índices creados:

    `(venv)$ make listar_indices`

## Correr API 

- Correr `georef-api`, utilizando un servidor de prueba (no apto para producción):
    
    `(venv)$ flask run`

## Pruebas

- Pruebas unitarias:

    `(venv) $ python -m unittest`
  
- Consumir la API mediante la herramienta CURL:

    `$ curl localhost:5000/api/v1.0/direcciones?direccion=cabral+500`
  
    `$ curl localhost:5000/api/v1.0/provincias`
