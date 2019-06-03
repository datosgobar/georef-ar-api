# Entornos productivos

Para instalar la API de Georef en un entorno productivo, es necesario completar todos los pasos detallados en la [guía de instalación y ejecución](georef-api-development.md). Luego, seguir los siguientes pasos adicionales:

## 1. Configurar servicio para systemd
Copiar el archivo [`config/georef-ar-api.service`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-ar-api.service) a `/etc/systemd/system/` y configurarlo. **Notar los campos marcados entre '`<`' y '`>`'**, que deben ser reemplazados por los valores apropiados.

Luego, activar y arrancar el nuevo servicio:
```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable georef-ar-api
$ sudo systemctl start georef-ar-api
```

Una vez ejecutados los comandos, comprobar que la API esté funcionando:
```bash
$ curl localhost:5000/api/provincias
```

El servicio instalado asegura que la API sea ejecutada al reinicar el sistema operativo, y se encarga de automáticamente almacenar todos los *logs* generados por la API. Los mismos pueden ser consultados utilizando:
```bash
$ sudo journalctl -u georef-ar-api
```

Ver `man journalctl` para más detalles de uso.

## 2. Configurar Nginx
Resulta conveniente configurar un servidor Nginx que actúe como receptor de todas las consultas destinadas al servidor de la API. El servidor Nginx permite controlar tamaños máximos de consultas y respuestas, establecer *caches*, y muchas más utilidades. Asumiendo que se instaló Nginx utilizando el administrador de paquetes (`apt`), seguir los siguientes pasos:

### 2.1 Crear archivo de configuración
Primero, crear `/etc/nginx/sites-available/georef-ar-api.nginx` tomando como base la configuración del archivo [`georef-ar-api.nginx`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-ar-api.nginx).

### 2.2 (Opcional) Configurar *cache*
Si se desea activar el uso del *cache* de Nginx, descomentar las líneas contentiendo las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-ar-api.nginx` creado. Luego, activar el *cache* `georef` agregando la siguiente línea al archivo de configuración `nginx.conf` (sección `http`):

```nginx
proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
```

Finalmente, crear el directorio `/data/nginx/cache`.

### 2.3 Activar y validar la configuración
Generar un link simbólico a la configuración de Georef:
```bash
$ sudo ln -s /etc/nginx/sites-available/georef-ar-api.nginx /etc/nginx/sites-enabled/georef-ar-api.nginx
```

Validar la configuración:
```bash
$ sudo nginx -T
```

Finalmente, reiniciar Nginx:
```bash
$ sudo systemctl restart nginx.service
```

Una vez ejecutados los comandos, comprobar nuevamente que la API esté funcionando, en el puerto 80 estándar:
```bash
$ curl localhost/api/provincias
```
