---
title: "Historial de versiones"
---

Las entradas de v2.0 y v2.1 salen del historial de commits de la rama `development` del repositorio; al 25/09/2026 no tienen tag de versión en git. Las entradas 0.5.4 y 0.5.5 salen de los commits entre los tags correspondientes de la rama `master`.

## **v2.1** - 2026/06/02
Commits principales: `4f57b83`, `1e31ad4`, `2bbc5c5`, `1e4a2b8`, `8ba6954`.

- Agrega el recurso `/establecimientos`, que busca establecimientos educativos e instituciones universitarias a la vez (`4f57b83`).
- Agrega un decorador de obsolescencia: `/municipios`, `/establecimientos-educativos` e `/instituciones-universitarias` responden con los encabezados `Deprecation` y `Link` que indican el recurso sucesor (`1e31ad4`).
- Publica la API bajo `/api/v2.1`; la v2.0 queda en `/api/v2.0` sin `/establecimientos` (`2bbc5c5`).
- Corrige el procesamiento de parámetros en el decorador que registra los pedidos en el log (`1e4a2b8`).
- Agrega las entidades nuevas a las descargas completas (`8ba6954`).
- Antes de v2.1, en la misma rama: agrega el filtro `localidad` a `/direcciones` (`8172360`), corrige la `nomenclatura` de `/ubicacion` (`7366ab8`, #240), cambia la indexación de `categoria` en gobiernos locales (`e0ee2b2`) y actualiza la versión de datos del ETL (`97a6104`).

## **v2.0** - 2025/08/26
Commit de cambio de versión: `b6acae5` ("Cambia a v2.0"). Incluye el trabajo de la rama `development` desde 2023:

- Reemplaza municipios por gobiernos locales y agrega el recurso `/gobiernos-locales` (`22bf910`); luego reincorpora `/municipios` por compatibilidad (`ce6bbce`, `c49bf6c`).
- Agrega el filtro `categoria` a gobiernos locales (`8fac115`) y a asentamientos (`7678789`), y vincula localidades y asentamientos por categoría (`e306edb`).
- Agrega unidades geoestadísticas: `/aglomerados`, `/fracciones-censales` y `/radios-censales` (`413e1cd`, `5d36f00`, `463e253`, `33cab12`).
- Agrega el recurso `/cuadras` (`5a9236e`) y los datos de localidad en calles y cuadras (`1796f92`, `7244f3c`).
- Agrega establecimientos educativos (`7900b22`), instituciones universitarias (`fa2a344`) y el recurso `/establecimientos-cercanos` (`4ad70aa`).
- Cambia la longitud de los IDs de calles y cuadras (`5fea6df`) y adapta el código a IDs de calles de longitud variable (`7cfa6bc`).
- `/direcciones`: agrega el campo `localidad` (`fa5cd5e`), la localidad en `nomenclatura` (`36406ac`), la georreferenciación desplazada del eje de calle (`5c9a246`, `1ea732d`) con el parámetro `desplazar` (`e470bda`, `7b029a4`), el formato `shp` (`ebb86a5`), y elimina el parámetro `verificar` (`7c4a2e8`).
- `/ubicacion`: agrega calle y altura (`6311d79`) y el parámetro `division` (`0a4c67f`).
- Agrega el formato GeoPackage, `gpkg` (`330c4a4`).
- Actualiza librerías e imagen de Docker (`bea99dd`, `fe46512`).

## **0.5.5** - 2025/02/24
- Adapta los parámetros de ID de localidades y asentamientos: ambos (provistos por BAHRA) pueden tener 8 o 10 caracteres; los de asentamientos son alfanuméricos y los de localidades, numéricos (`b1911b6`, #232).
- Modifica las URLs de las fuentes a indexar, de los archivos de sinónimos y de las descargas (`4b239a5`, `29d92f1`, `4eef435`).
- Modifica parámetros y fuente de datos de la configuración de Docker (`5fa0a71`).

## **0.5.4** - 2024/10/07
- Corrige la validación del parámetro `id` para asentamientos (`791fb1c`, #228).
- Completa las descargas de archivos completos: suma `cuadras` y el formato `ndjson` (`db19ca8`).
- Actualiza Flask a 2.0.0 (`6818c00`) y corrige dependencias de la imagen de Docker (`4cda858`).
- Agrega configuración para Docker: archivo `.env` y mapeo de puerto del contenedor de Elasticsearch (`4b7d53e`, `cf044cd`).
- Corrige un error con direcciones de altura 0 (`55ed138`).
- Agrega a la documentación la ruta del recurso de descargas en la especificación OpenAPI y enlaces de descarga (`d7e1068`).

## **0.5.3** - 2019/05/16
- Agrega campo `parametros` a todas las respuestas de la API. El campo contiene los valores (interpretados) de los parámetros recibidos por la API en la consulta.
- Agrega archivo `.prj` a respuestas de consultas en formato *Shapefile*.
- Modifica el valor del campo de respuesta `altura.valor` en el recurso `/direcciones`. El campo ahora contiene la altura de la dirección en formato numérico, es decir, `int` o `float`. Si la dirección no contiene una altura numérica (por ejemplo, "Calle 15 S/N"), el valor del campo es `null`.

## **0.5.2** - 2019/05/14
- Agrega parámetro `localidad` a recurso `/direcciones`.

## **0.5.1** - 2019/05/10
- Corrige campos CSV del recurso `/localidades-censales`.
- Corrige valor de `cantidad` para consultas al recurso `/asentamientos`.

## **0.5.0** - 2019/05/09
- Agrega recurso `/localidades-censales`. El nuevo recurso ofrece un listado de localidades censales definidas por INDEC.
- Agrega recurso `/asentamientos`. El nuevo recurso contiene la enteridad de la base [BAHRA](http://www.bahra.gob.ar/), y sus parámetros y formatos de respuesta son idénticos a los de `/localidades`.
- Agrega campo `localidad_censal` a respuestas de recursos `/localidades`, `/calles`, y `/direcciones`. El campo permite acceder al nombre y ID de la localidad censal de la localidad o calle correspondiente.
- Agrega nuevo parámetro `localidad_censal` a `/localidades`, `/calles` y `/direcciones`. El parámetro permite filtrar direcciones, calles y localidades por localidad censal, lo cual en algunos casos ofrece un mayor grado de precisión que utilizar `departamento`.
- Mejora la precisión de la georreferenciación inversa (`/ubicacion`) como resultado de haber actualizado la versión de Elasticsearch.
- Actualiza versión de datos de ETL a `12.0.0`.
- Mejora interpretación de direcciones (`georef-ar-address` versión `0.0.9`).

## **0.4.1** - 2019/04/25
- Agrega localidades de tipo `LCE` y `LSE` a recurso `/localidades`.
- Actualiza versión de datos de ETL a `11.0.0`.

## **0.4.0** - 2019/04/23
- Modifica fuente de datos utilizada para recurso `/direcciones`. Se aumentó considerablemente la cantidad de direcciones que pueden ser georreferenciadas.
- Actualiza versión de datos de ETL a `10.0.0`.
- Mejora interpretación de direcciones (`georef-ar-address` versión `0.0.8`).

## **0.3.3** - 2019/02/11
- Corrige error HTTP 500 lanzado cuando se utilizaban valores como "NaN" o "Inifinity" para parámetros `lat` y `lon` en `/ubicacion`.

## **0.3.2** - 2019/02/05
- El parámetro `interseccion` de los recursos `/provincias`, `/departamentos` y `/calles` ahora aceptan IDs de calles como parámetros.
- Modifica cantidad de máxima de consultas en una sola petición POST a 1000 (era 5000). El nuevo valor permite normalizar datos a una velocidad prácticamente igual a la anterior, pero con una menor carga a la infraestructura.

## **0.3.1** - 2019/01/29
- Mejora interpretación de direcciones (`georef-ar-address` versión `0.0.7`).
- Corrige error HTTP 500 lanzado en normalización de direcciones, en casos donde el comienzo y el fin de alturas de la calle comparten el mismo valor, y la dirección tiene ese valor exacto como altura.

## **0.3.0** - 2019/01/24
- Agrega XML como nuevo formato de respuesta de datos para todos los recursos. Para utilizarlo, agregar `formato=xml` a los parámetros de la URL.
- Agrega *Shapefile* como nuevo formato de respuesta de datos para todos los recursos (excepto `/direcciones` y `/ubicacion`). Para utilizarlo, agregar `formato=shp` a los parámetros de la URL. El archivo descargado contiene las geometrías e información de todas las entidades filtradas. Para más detalles, consultar [la documentación de descarga de geometrías](/georef-ar-api/shapefiles/).
- El parámetro `id` ahora acepta listas de IDs separadas por comas. Otros parámetros que aceptaban un ID también aceptan ahora listas de IDs.
- Actualiza versión de datos de ETL a `9.0.0`.
- Corrige mensajes de error equivocados.
- Cambios varios al recurso `/direcciones`:
	- Utilizando la librería [georef-ar-address](https://github.com/datosgobar/georef-ar-address), se mejoró el proceso de interpretación de las direcciones recibidas. Ahora, se aceptan más tipos de direcciones, y la API es capaz de detectar errores comunes de escritura. Para más detalles, consultar la nueva documentación de [normalización de direcciones](/georef-ar-api/addresses/).
	- Se removió el parámetro `tipo`.
	- Se modificó el campo de respuesta `altura` a un objecto `altura` que contiene los valores `valor` y `unidad.`
	- Se removieron los campos `nombre` y `id`, y se agregaron los nuevos campos objeto `calle`, `calle_cruce_1` y `calle_cruce_2`. Cada uno contiene los campos `nombre`, `id` y `categoria`, y representan las calles normalizadas que fueron detectadas en la dirección de entrada.
	- Se agregó el campo `piso`.
	- Se modificaron los nombres y el orden de los campos de respuesta en formato CSV.
- Cambios al recurso `/provincias`:
	- Se agregaron los campos `nombre_completo`, `iso_id`, `iso_nombre` y `categoria`.
- Cambios al recurso `/departamentos`:
	- Se agregaron los campos `nombre_completo` y `categoria`.
- Cambios al recurso `/municipios`:
	- Se agregaron los campos `nombre_completo` y `categoria`.
	- Parámetro `interseccion`: agrega `calle` como tipo de entidad posible a utilizar.
- Cambios al recurso `/localidades`:
	- Se modificó el nombre del campo `tipo` a `categoria`.
- Cambios al recurso `/calles`:
	- Se modificó el nombre del campo `tipo` a `categoria`.
	- Se modificó el nombre del parámetro `tipo` a `categoria`.
	- Agrega parámetro `interseccion`: permite buscar calles por intersección con geometrías de otras entidades.
- Cambios al recurso `/ubicacion`:
	 - Se removió el campo `fuente`, y se agregaron los campos `provincia.fuente`, `departamento.fuente` y `municipio.fuente`.

## **0.2.3** - 2018/12/11
- Modifica formato de respuestas CSV: todos los campos no-numéricos ahora son devueltos entre comillas dobles. El cambio permite a algunas herramientas manejar mejor los valores de IDs, que consisten enteramente de dígitos, pero deberían ser tratados como texto.
- El parámetro 'direccion' del recurso `/direcciones` ahora acepta direcciones con altura 0.
- Mejora la fidelidad de resultados por en búsquedas por nombre: algunos términos de búsqueda ahora excluyen a otros, aunque sean textualmente similares. Por ejemplo, buscar 'salta' no incluye resultados con 'santa', ya que los dos términos refieren a entidades claramente distintas.

## **0.2.2** - 2018/11/05
- El parámetro 'direccion' del recurso `/direcciones` ahora acepta direcciones sin altura (por ejemplo, "Avenida Santa Fe"). Este cambio permite utilizar la versión `POST` del recurso con mayor facilidad, en caso de tener grandes cantidades de datos con y sin alturas en un mismo conjunto.
- Mejoras a mensajes de error para parámetros 'direccion' e 'interseccion'.

## **0.2.1** - 2018/10/25
- Actualiza proceso de indexación para utilizar datos de ETL versión `6.0.0`.
- Agrega mensaje de error descriptivo para errores HTTP 405.
- Mejora parámetro 'campos': se permite especificar un prefixo para referirse a varios campos (por ejemplo, `provincia` para `provincia.id` y `provincia.nombre`).
- Agrega parámetro `interseccion`. El mismo permite buscar provincias, departamentos y municipios utilizando intersección de geometrías con otras entidades geográficas.
	- Se pueden buscar provincias por intersección con municipios y departamentos.
	- Se pueden buscar departamentos por intersección con provincias y municipios.
	- Se pueden buscar municipios por intersección con provincias y departamentos.
- Agrega nuevo campo de datos `provincia.interseccion` a recursos `/municipios` y `/departamentos`. El campo especifica qué porcentaje del área de la provincia ocupa la entidad en sí.
- Agrega nuevos recursos de descarga de datos completos. Estos recursos permiten descargar la totalidad de los datos utilizados por cada recurso, en distintos formatos. Por ejemplo, para descargar los datos de provincias, se puede acceder a las siguientes URLs:
	- [https://apis.datos.gob.ar/georef/api/v1.0/provincias.json](https://apis.datos.gob.ar/georef/api/v1.0/provincias.json)
	- [https://apis.datos.gob.ar/georef/api/v1.0/provincias.csv](https://apis.datos.gob.ar/georef/api/v1.0/provincias.csv)
	- [https://apis.datos.gob.ar/georef/api/v1.0/provincias.geojson](https://apis.datos.gob.ar/georef/api/v1.0/provincias.geojson)

## **0.2.0** - 2018/09/21
- Remueve campo 'departamento' de la entidad municipio. Esto se debe a que los departamentos no son padres jerárquicos de los municipios.
- Agrega parámetro `orden` a recursos `/calles` y `/direcciones`.
- Agrega formato GeoJSON a recurso `/direcciones`.
- Agrega conjuntos de campos predefinidos al parámetro `campos`, los valores posibles son:
	- `basico`
	- `estandar` (utilizado por defecto)
	- `completo`
- Mueve campo de respuestas `fuente` a conjunto `completo`.
- Permite el uso del parámetro `aplanar` en respuestas GeoJSON.

## **0.1.6** - 2018/09/07
- Actualiza proceso de indexación para utilizar datos de ETL versión `4.0.0`.
- Modifica manejo de altura en recurso `/direcciones`. La nueva versión del recurso intenta ubicar altura dentro de los extremos de la calle tomando en consideración que los datos pueden no siempre estar completos (o ser ideales). Este cambio también afecta la efectividad de la geolocalización de direcciones.

## **0.1.5** - 2018/09/04
- Mejora mensajes de errores para varios casos:
	- Acceso a recursos inexistentes (por ejemplo: `/provincia`).
	- Valores inválidos para parámetros con elección limitada de valores (por ejemplo, `orden`).
	- Listas de operaciones bulk inválidas.
	- Direcciones de calles malformadas.
- Agrega API de paginado.
	- Nuevo parámetro: `inicio`.
	- Los resultados ahora incluyen tres metadatos: `cantidad`, `total` e `inicio`.

## **0.1.4** - 2018/08/23
- Se modificó la interpretación del parámetro `direccion` del recurso `/direcciones`:
	- Se ignoran ítems entre paréntesis y ocurrencias de "N°"
	- Se separa el texto utilizando "-", "," y "B°", y se intenta extraer una dirección (nombre + altura) de cada fragmento.

## **0.1.3** - 2018/08/21
- Se modificaron los siguientes campos:
	- `centroide_lat` y `centroide_lon` ahora están anidados.
	- Los campos `altura_inicio_derecha`, `altura_fin_derecha`, etc. ahora están anidados.
- Se agregó una validación de valores repetidos para parámetro `campos`.
- El recurso `/provincias` ahora acepta el parámetro `aplanar`.

## **0.1.2** - 2018/08/16
- Se removió `d` como stopword en Elasticsearch.

## **0.1.1** - 2018/08/15
- Se modificaron los siguientes campos:
	- `lat` ahora es `centroide_lat`.
	- `lon` ahora es `centroide_lon`.
	- Los campos `inicio_derecha`, `fin_derecha`, etc. ahora comienzan con `altura_`.

## **0.1.0** - 2018/08/14
- Versión inicial.
