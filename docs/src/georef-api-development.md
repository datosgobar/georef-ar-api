# Guía de instalación para desarrolladores

En este documento se detallan los pasos a seguir si se desea configurar un servidor de API Georef propio.

## Dependencias

- [Elasticsearch >=6.4.2](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [Nginx](https://nginx.org/) *(para entornos productivos)*

## Instalación

### 1. Elasticsearch

Para instalar Elasticsearch, seguir las siguientes instrucciones en uno o más servidores (nodos).

#### 1.1 Instalar el entorno de ejecución para Java:
```bash
$ sudo apt install default-jre
```

#### 1.2 Instalar Elasticsearch

Instalar Elasticsearch e iniciar el servicio con `systemctl`:
```bash
$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.4.2.deb
$ sudo dpkg -i elasticsearch-6.4.2.deb
$ sudo systemctl enable elasticsearch
```
#### 1.3 Aplicar las configuraciones recomendadas

Editar el archivo  `/etc/elasticsearch/elasticsearch.yml` (el valor de `node.name` debe ser único por nodo):

```text
node.name: node-1
http.max_content_length: 100mb
```

Editar el archivo `/etc/elasticsearch/jvm.options` (siguiendo las [recomendaciones de Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html)):
```text
# Tamaño del heap size de la JVM
# Se recomienda utilizar siempre el mismo valor como mínimo y máximo
# Ejemplo: 4 GB
-Xms4g
-Xmx4g
```

### 2. Repositorio y dependencias

#### 2.1 Clonar el repositorio:
```bash
$ git clone https://github.com/datosgobar/georef-ar-api.git
$ cd georef-ar-api
```

#### 2.2 Crear un entorno virtual y activarlo
```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

#### 2.3 Instalar dependencias con `pip`
```bash
(venv) $ pip3 install -r requirements.txt -r requirements-dev.txt
```

#### 2.4 Copiar el archivo de configuración
```bash
(venv) $ cp config/georef.example.cfg config/georef.cfg
```

Luego, completar el archivo `config/georef.cfg` con los valores apropiados.

#### 2.5 Copiar el archivo de configuración de logs
```bash
(venv) $ cp config/logging.example.ini config/logging.ini
```

Luego, completar el archivo `config/logging.ini` con los valores apropiados. Los valores por defecto son válidos y pueden ser utilizados en entornos productivos.

### 3. Crear los índices
Generar índices de entidades y calles:
```bash
(venv) $ make index
```
        
Listar los índices creados, y otros datos adicionales:
```bash
(venv) $ make print_index_stats
```
	
### 4. (Opcional) Re-indexar datos
Si se modifican los archivos de datos JSON, es posible re-indexarlos sin borrar los índices ya existentes. Dependiendo del comportamiento que se desee, se debe tomar una opción:

#### Indexar datos nuevos
Si se desea actualizar los índices con los nuevos datos, solo si los datos entrantes son más recientes, se puede utilizar nuevamente:
  
```bash
(venv) $ make index
```

#### Forzar re-indexado
Si se desea forzar un re-indexado, es decir, si se desea indexar los datos nuevamente sin importar la fecha de creación, se debe utilizar la siguiente receta:

```bash
(venv) $ make index_forced
```

La receta `index_forced` intenta utilizar un archivo de respaldo guardado anteriormente si no pudo acceder a los archivos especificados en `config/georef.cfg`. El uso de la receta es recomendado cuando se requiere re-indexar los datos incondicionalmente, algunas situaciones donde esto es necesario son:

- Modificación de la estructura de los archivos de datos
- Modificación de *mappeos* de tipos de Elasticsearch
- Modificación de analizadores de texto de Elasticsearch
- Modificación de listado de sinónimos
- Modificación de listado de términos excluyentes


Cualquiera de las dos opciones también permite indexar datos selectivamente: se debe especificar el nombre del índice a crear/re-indexar. Por ejemplo:
```bash
(venv) $ make index INDEX_NAME=localidades
(venv) $ make index_forced INDEX_NAME=calles
```

Los nombres de los índices disponibles son:

- `provincias`
- `provincias-geometria`
- `departamentos`
- `departamentos-geometria`
- `municipios`
- `municipios-geometria`
- `localidades`
- `calles`
- `intersecciones`

### 5. Correr API 
#### Entornos de desarrollo
Correr la API de Georef utilizando un servidor de prueba (no apto para producción):
```bash
(venv) $ make start_dev_server
```

O También:
```bash
(venv) $ make start_gunicorn_dev_server
```

#### Entornos productivos
##### 5.1 Configurar servicio `georef-ar-api` para `systemd`
Copiar el archivo [`config/georef-ar-api.service`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-ar-api.service) a `/etc/systemd/system/` y configurarlo. Notar los campos marcados entre '`<`' y '`>`', que deben ser reemplazados por el usuario.

##### 5.2 Activar y arrancar el servicio
```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable georef-ar-api.service
$ sudo systemctl start georef-ar-api.service
```

##### 5.3 Configurar `nginx`
Primero, crear `/etc/nginx/sites-available/georef-ar-api.nginx` tomando como base la configuración del archivo [`georef-ar-api.nginx`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-ar-api.nginx).

##### 5.4 (Opcional) Crear cache para `nginx`
Si se desea activar el uso del cache de `nginx`, descomentar las líneas contentiendo las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-ar-api.nginx` creado. Luego, activar el cache `georef` agregando la siguiente línea al archivo de configuración `nginx.conf` (sección `http`):

```nginx
proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
```

Finalmente, crear el directorio `/data/nginx/cache`.

##### 5.5 Activar y validar configuración `nginx`
Generar un link simbólico a la configuración del sitio:
```bash
$ sudo ln -s /etc/nginx/sites-available/georef-ar-api.nginx /etc/nginx/sites-enabled/georef-ar-api.nginx
```

Validar la configuración:
```bash
$ sudo nginx -T
```

Reiniciar Nginx:
```bash
$ systemctl restart nginx.service
```

## Tests
Para ejecutar los tests unitarios (el servicio Elasticsearch debe estar activo y con los datos apropiados cargados):
```bash
(venv) $ make test
```

Para más información sobre los tests, ver el archivo [`tests/README.md`](https://github.com/datosgobar/georef-ar-api/blob/master/tests/README.md).


Para comprobar que no existan errores comunes en el código, y que su estilo sea correcto:
```bash
(venv) $ make code_checks
```

## Archivos de datos

- La estructura de los archivos de datos JSON utilizados por Georef está detallada en [este documento](georef-api-data.md).

- El archivo de configuración `config/georef.cfg` debe especificar una ruta local o una URL externa para cada archivo de datos JSON. Notar que los valores por defecto (en `georef.example.cfg`) utilizan el portal de descargas `infra.datos.gob.ar`, que siempre provee la última versión de los archivos JSON disponibles. La rama `master` de `georef-ar-api` siempre se mantiene compatible con la última versión de los datos disponibles en `infra.datos.gob.ar`.

- El archivo de configuración `config/georef.cfg` también debe especificar la URL del archivo de sinónimos para utilizar al momento de indexar campos de texto en Elasticsearch. El valor por defecto en `georef.example.cfg` puede ser utilizado, ya que utiliza la versión del archivo almacenado en `infra.datos.gob.ar`. El mismo criterio se aplica al archivo de términos excluyentes.
