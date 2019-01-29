# Historial de versiones

## **0.3.1** - 2019/01/29
- Mejora interpretación de direcciones (`georef-ar-address` versión `0.0.7`).
- Corrige error HTTP 500 lanzado en normalización de direcciones, en casos donde el comienzo y el fin de alturas de la calle comparten el mismo valor, y la dirección tiene ese valor exacto como altura.

## **0.3.0** - 2019/01/24
- Agrega XML como nuevo formato de respuesta de datos para todos los recursos. Para utilizarlo, agregar `formato=xml` a los parámetros de la URL.
- Agrega *Shapefile* como nuevo formato de respuesta de datos para todos los recursos (excepto `/direcciones` y `/ubicacion`). Para utilizarlo, agregar `formato=shp` a los parámetros de la URL. El archivo descargado contiene las geometrías e información de todas las entidades filtradas. Para más detalles, consultar [la documentación de descarga de geometrías](shapefiles.md).
- El parámetro `id` ahora acepta listas de IDs separadas por comas. Otros parámetros que aceptaban un ID también aceptan ahora listas de IDs.
- Actualiza versión de datos de ETL a `9.0.0`.
- Corrige mensajes de error equivocados.
- Cambios varios al recurso `/direcciones`:
	- Utilizando la librería [georef-ar-address](https://github.com/datosgobar/georef-ar-address), se mejoró el proceso de interpretación de las direcciones recibidas. Ahora, se aceptan más tipos de direcciones, y la API es capaz de detectar errores comunes de escritura. Para más detalles, consultar la nueva documentación de [normalización de direcciones](addresses.md).
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
	- [https://apis.datos.gob.ar/georef/api/provincias.json](https://apis.datos.gob.ar/georef/api/provincias.json)
	- [https://apis.datos.gob.ar/georef/api/provincias.csv](https://apis.datos.gob.ar/georef/api/provincias.csv)
	- [https://apis.datos.gob.ar/georef/api/provincias.geojson](https://apis.datos.gob.ar/georef/api/provincias.geojson)

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
