# georef-api Swagger UI

Página Swagger UI para la documentación OpenAPI de `georef-api`. La documentación se puede acceder visitando [este enlace](https://datosgobar.github.io/georef-api/).

## Archivos

`docs/openapi.json`: Documentación para `georef-api` en formato OpenAPI 3.

`src/`: Archivos de `swagger-ui-dist` modificados para la documentación de `georef-api`.

## Desarrollo

1. Clonar la rama `gh-pages` del repositorio:
```bash
$ git clone -b gh-pages git@github.com:datosgobar/georef-api.git
$ cd georef-api
```

2. Instalar las dependencias:
```bash
$ npm install --global gulp-cli
$ npm install
```

3. Realizar los cambios deseados a los archivos del directorio `src/`.

4. Copiar los archivos de la página al directorio raíz del proyecto:
```bash
$ gulp build
```
El comando ejecutado copia los archivos de `swagger-ui-dist`, `swagger-ui-themes` y `src/` al directorio raíz del proyecto, en el orden mencionado. Los archivos de `src/` toman proridad y sobreescriben archivos existentes con el mismo nombre, si los hay.

5. Subir los cambios a la rama `gh-pages`:
```bash
$ git add ...
$ git commit -m "..."
$ git push origin gh-pages
```
