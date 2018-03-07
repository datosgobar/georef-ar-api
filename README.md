# georef-api Swagger UI

`docs/openapi.json`: Documentación para `georef-api` en formato OpenAPI 3.
`src/`: Archivos de `swagger-ui-dist` modificados para la documentación de `georef-api`.

## Desarrollo

Para combinar archivos de `swagger-ui-dist`, `swagger-ui-themes` y `src/` en la raiz del proyecto, ejecutar `gulp build`.  Los archivos de `src/` se copian últimos, y sobreescriben otros archivos existentes.