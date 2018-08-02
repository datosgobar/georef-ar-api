# Deploy Georef API

## Dependencias

- [Elasticsearch >=6.2.0](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Gunicorn](http://gunicorn.org/)
- [Nginx](https://nginx.org/)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGIS 2.3](http://postgis.net/install/)

## Instalación

### Datos

En [este documento](georef-api-data.md) se detalla el modelo de datos utilizado por la API y las URLs donde se encuentran publicados. 

### Base de datos

Crear una base de datos en PostgreSQL con la extensión PostGIS.

Ejemplo utilizando `georef_api` como nombre para la base de datos:

```plsql
-- Crear la base de datos
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregar PostGIS a la base de datos creada
CREATE EXTENSION postgis;
```

### Repositorio y dependencias

- Clonar el repositorio:

    `$ git clone https://github.com/datosgobar/georef-api.git`

	`$ cd georef-api`
    
- Crear un entorno virtual y activarlo:

    `$ python3 -m venv venv`
    
    `$ . venv/bin/activate`

- Instalar dependencias con `pip`:
    
    `(venv) $ pip3 install -r requirements.txt`

- Copiar el archivo de configuración de logs:

    `(venv) $ cp config/logging.example.ini config/logging.ini`
	
- Completar el archivo `config/logging.ini` con los datos apropiados.
    
- Copiar el archivo de configuración:

    `(venv) $ cp config/georef.example.cfg config/georef.cfg`
    
- Completar el archivo `config/georef.cfg` con los datos apropiados.
 
### Elasticsearch

Para instalar Elasticsearch, seguir las siguientes instrucciones en uno o más servidores (nodos).

- Instalar el entorno de ejecución para Java:

    `$ sudo apt install default-jre`

- Instalar Elasticsearch:

    `$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.deb`

    `# dpkg -i elasticsearch-6.2.0.deb`

- Opcionalmente, aplicar las configuraciones recomendadas. El valor de `node.name` debe ser único por nodo.

    `$ sudo $EDITOR /etc/elasticsearch/elasticsearch.yml`

    ```
    cluster.name: georef-api
    node.name: node-1
    http.max_content_length: 100mb
    ```

    `$ sudo $EDITOR /etc/elasticsearch/jvm.options` (siguiendo las recomendaciones de [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html))

    ```
    # Tamaño del heap size de la JVM
    # Se recomienda utilizar siempre el mismo valor como mínimo y máximo
    # Ejemplo: 4 GB
    -Xms4g
    -Xmx4g
    ```

### Archivos de datos

- Se debe contar con los archivos de datos para entidades y calles mencionados al comienzo de la guía, y sus rutas deben estar configuradas en el archivo `config/georef.cfg`.

- Adicionalmente, se debe crear un archivo `georef_synonyms.txt`, en la ubicación del archivo de configuración de Elasticsearch (`$ES_HOME/config`), en cada nodo. El archivo contiene la base de sinónimos utilizados al momento de indexar documentos. Su contenido puede ser vacío, y debe ser idéntico por cada nodo.

### Cargar las funciones SQL

- Cargar las funciones SQL necesarias para el funcionamiento de la API:

	`(venv) $ make load_sql`

### Crear los índices
    
- Generar índices de entidades y calles.

    `(venv) $ make index`
        
- Listar los índices creados, y otros datos adicionales:

    `(venv) $ make index_stats`

## Correr API

Agregar la configuración de los servicios `gunicorn` y `nginx`.

- Completar y modificar el archivo `config/georef-api.service` [de este repositorio](../config/georef-api.service). Notar los campos marcados entre '<' y '>'. El archivo se debe copiado a `/etc/systemd/system/` para poder ser utilizado con `systemctl`.

- Activar y arrancar el servicio:
  
    `# systemctl daemon-reload`

	`# systemctl enable georef-api.service`

    `# systemctl start georef-api.service`

- Para `nginx`, crear `/etc/nginx/sites-available/georef-api` tomando como base la configuración del archivo `georef-api.nginx` [de este repositorio](../config/georef-api.nginx).

- Para activar el uso del cache de `nginx`, descomentar las líneas contentiendo las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-api` creado. Luego, activar el cache `georef` agregando la siguiente línea al archivo de configuración `nginx.conf` (sección `http`):
    ```
    proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
    ```
    Finalmente, crear el directorio `/data/nginx/cache`.

- Generar un link simbólico a la configuración del sitio:

    `# ln -s /etc/nginx/sites-available/georef-api /etc/nginx/sites-enabled/georef-api`

- Validar la configuración:

    `# nginx -t`

- Cargar la nueva configuración:

    `# nginx -s reload`

- Reiniciar Nginx:

    `# systemctl restart nginx.service`

## Pruebas

- Pruebas unitarias (los servicios Elasticsearch y PostgreSQL deben estar activos y con los datos apropiados cargados):

    `(venv) $ make test_all`
