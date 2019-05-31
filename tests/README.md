# georef-ar-api - Tests `unittest`

El directorio `tests/` de `georef-ar-api` contiene todos los tests unitarios utilizados para comprobar que la API está funcionando correctamente luego de realizar cambios al código. Los tests están separados en dos categorías principales, indicadas en el comienzo del nombre de cada archivo:

- **Tests Mock/Offline**: Estos tests pueden ser ejecutados sin contar con una instancia de Elasticsearch corriendo. No utilizan datos reales. Los tests de esta categoría cuentan con nombres de archivo de la forma `test_mock_{}.py`, y siempre heredan de la clase `GeorefMockTest`.

- **Tests En Vivo/Online**: Estos tests requieren de una instancia de Elasticsearch corriendo, con los datos del ETL cargados correctamente. Los tests de esta categoría cuentan con nombres de archivo de la forma `test_search_{}.py`, y siempre heredan de la clase `GeorefLiveTest`. Si algún dato cambia de forma tal que rompa un test, se debe modificar el test para que funcione correctamente de nuevo, teniendo en cuenta de que debe seguir validando la misma parte de la funcionalidad de la API.

Para ejecutar todos los tests desde la raíz del proyecto, utilizar:
```bash
$ make test
```

Para ejecutar solo los tests que **no** requieren Elasticsearch:
```bash
$ make test_mock
```
