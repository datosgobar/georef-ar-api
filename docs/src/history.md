# Historial de versiones

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
