---
title: "Entornos productivos"
---

Para instalar la API Georef en producción, primero completá la [instalación manual](/georef-ar-api/georef-api-development/#opción-b-instalación-manual) de la guía de instalación. Después seguí estos pasos.

:::caution[A validar]
Esta guía describe un despliegue con systemd y Nginx a partir de los archivos de `config/` de la rama `development`. No pudimos verificar cómo está desplegada hoy la instancia pública de `apis.datos.gob.ar` (que además pasa por un gateway con límites de uso).
:::

## 1. Configurar servicio para systemd
Copiá [`config/georef-ar-api.service`](https://github.com/datosgobar/georef-ar-api/blob/development/config/georef-ar-api.service) a `/etc/systemd/system/` y configuralo. **Reemplazá los campos marcados entre `<` y `>`** (usuario y ruta al repositorio) por los valores de tu servidor. El servicio corre `gunicorn` con 4 *workers* `gevent` en el puerto 5000.

Después, activá y arrancá el servicio:
```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable georef-ar-api
$ sudo systemctl start georef-ar-api
```

Comprobá que la API responda:
```bash
$ curl localhost:5000/api/v2.1/provincias
```

El servicio arranca la API cuando se reinicia el sistema y guarda automáticamente los *logs*. Para consultarlos:
```bash
$ sudo journalctl -u georef-ar-api
```

Más detalles en `man journalctl`.

## 2. Configurar Nginx
Conviene poner Nginx delante de la API para recibir todas las consultas: te permite controlar tamaños máximos de pedidos y respuestas, usar *cache* y más. Si instalaste Nginx con `apt`, seguí estos pasos:

### 2.1 Crear archivo de configuración
Creá `/etc/nginx/sites-available/georef-ar-api.nginx` a partir de [`config/georef-ar-api.nginx`](https://github.com/datosgobar/georef-ar-api/blob/development/config/georef-ar-api.nginx).

### 2.2 (Opcional) Configurar *cache*
Para usar la *cache* de Nginx, descomentá las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-ar-api.nginx`. Después activá la *cache* `georef` agregando esta línea a `nginx.conf` (sección `http`):

```nginx
proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
```

Por último, creá el directorio `/data/nginx/cache`.

### 2.3 Activar y validar la configuración
Creá un enlace simbólico a la configuración:
```bash
$ sudo ln -s /etc/nginx/sites-available/georef-ar-api.nginx /etc/nginx/sites-enabled/georef-ar-api.nginx
```

Validá la configuración:
```bash
$ sudo nginx -T
```

Y reiniciá Nginx:
```bash
$ sudo systemctl restart nginx.service
```

Comprobá que la API responda en el puerto 80:
```bash
$ curl localhost/api/v2.1/provincias
```
