# georef-ar-pi - Documentación

Este directorio contiene todos los archivos relacionados a la documentación de `georef-ar-api`.

## Archivos

El propósito de cada archivo/directorio incluido se detalla a continuación:
- `open-api/`:  Contiene el archivo de documentación OpenAPI, y archivos de la página Swagger UI generada a partir del mismo. Para más información, acceder al archivo [REAMDE.md](open-api/README.md) dentro del directorio.
- `src/`: Contiene archivos Markdown que documentan el uso y desarrollo de `georef-ar-api`. También contiene imágenes y archivos CSS necesarios para generar las páginas de documentación HTML utilizando *Read the Docs*.
- `.gitignore`: Se asegura que el directorio `site/` (donde se generan inicialmente las páginas *Read the Docs*) no se incluya en el repositorio remoto.
- `*`: Cualquier otro archivo o directorio forma parte de las páginas de documentación generadas por *Read the Docs*. Estos contenidos están contenidos directamente bajo el directorio `docs/` para permitir su uso con GitHub Pages.

## Desarrollo de Documentación

Luego de editar/crear cualquier archivo `.md` dentro de `src/`, se deben actualizar las páginas *Read the Docs*, y luego se deben cargar los archivos a GitHub Pages para que puedan ser accedidos a través de [https://datosgobar.github.io/georef-ar-api](https://datosgobar.github.io/georef-ar-api). Para hacer esto, seguir los siguientes pasos:

1. Desde la raíz del proyecto, activar un entorno virtual Python y luego instalar las dependencias necesarias:
```bash
(venv) $ pip install -r requirements-docs.txt
```

2. Generar las nuevas páginas con *Read the Docs*:
```bash
(venv) $ make docs
```

3. Subir los cambios a la rama `master`:
```bash
(venv) $ git add docs/
(venv) $ git commit -m "<mensaje> [skip ci]"
(venv) $ git push origin master
```
