# Historial de versiones

## 0.2.0
- Remueve campo 'departamento' de la entidad municipio. Esto se debe a que los departamentos no son padres jerárquicos de los municipios.
- Agrega parámetro `orden` a recursos `/calles` y `/direcciones`.
- Agrega formato GeoJSON a recurso `/direcciones`.
- Agrega conjuntos de campos predefinidos al parámetro `campos`: los valores posibles son:
	- `basico`
	- `estandar` (utilizado por defecto)
	- `completo`
- Mueve campo de respuestas `fuente` a conjunto `completo`.
- Permite el uso del parámetro `aplanar` en respuestas GeoJSON.

## 0.1.6
- Actualiza proceso de indexación para utilizar datos de ETL versión `4.0.0`.
- Modifica manejo de altura en recurso `/direcciones`. La nueva versión del recurso intenta ubicar altura dentro de los extremos de la calle tomando en consideración que los datos pueden no siempre estar completos (o ser ideales). Este cambio también afecta la efectividad de la geolocalización de direcciones.

## 0.1.5
- Mejora mensajes de errores para varios casos:
	- Acceso a recursos inexistentes (por ejemplo: `/provincia`).
	- Valores inválidos para parámetros con elección limitada de valores (por ejemplo, `orden`).
	- Listas de operaciones bulk inválidas.
	- Direcciones de calles malformadas.
- Agrega API de paginado.
	- Nuevo parámetro: `inicio`.
	- Los resultados ahora incluyen tres metadatos: `cantidad`, `total` e `inicio`.

## 0.1.4
- Se modificó la interpretación del parámetro `direccion` del recurso `/direcciones`:
	- Se ignoran ítems entre paréntesis y ocurrencias de "N°"
	- Se separa el texto utilizando "-", "," y "B°", y se intenta extraer una dirección (nombre + altura) de cada fragmento.

## 0.1.3
- Se modificaron los siguientes campos:
	- `centroide_lat` y `centroide_lon` ahora están anidados.
	- Los campos `altura_inicio_derecha`, `altura_fin_derecha`, etc. ahora están anidados.
- Se agregó una validación de valores repetidos para parámetro `campos`.
- El recurso `/provincias` ahora acepta el parámetro `aplanar`.

## 0.1.2
- Se removió `d` como stopword en Elasticsearch.

## 0.1.1
- Se modificaron los siguientes campos:
	- `lat` ahora es `centroide_lat`.
	- `lon` ahora es `centroide_lon`.
	- Los campos `inicio_derecha`, `fin_derecha`, etc. ahora comienzan con `altura_`.

## 0.1.0
- Versión inicial.
