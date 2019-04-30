# georef-ar-api Swagger UI

Página Swagger UI para la documentación OpenAPI de `georef-ar-api`. La documentación se puede acceder visitando [este enlace](https://datosgobar.github.io/georef-ar-api/open-api).

## Archivos

`spec/openapi.json`: Documentación para `georef-ar-api` en formato OpenAPI 3.

`src/`: Archivos de `swagger-ui-dist` modificados para la documentación de `georef-ar-api`.

## Crear/Actualizar página Swagger UI

**Nota**: Si solo se modifica el archivo `openapi.json`, **no** es necesario re-generar la página Swagger UI. La re-generación solo es útil si se necesita cambiar algún aspecto estético o estructural de la misma.

1. Desde la raíz del proyecto, acceder al directorio `open-api`:
```bash
$ cd docs/open-api
```

2. Instalar las dependencias. Se requiere tener `npm` instalado.
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

5. Subir los cambios a la rama `master`:
```bash
$ git add ...
$ git commit -m "..."
$ git push origin master
```

## Herramientas

Para validar el archivo `openapi.json` desde la consola de comandos, seguir las siguientes instrucciones:

1. Instalar las dependencias:
```bash
$ npm install --global swagger-cli
```

2. Ejecutar la herramienta de validación:
```
$ swagger-cli validate spec/openapi.json
```

Otra opción es utilizar [Swagger Editor](https://editor.swagger.io/) (copiar y pegar el código JSON en el editor).
