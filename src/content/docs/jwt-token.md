---
title: "Tokens JWT"
---

Históricamente, los organismos de la Administración Pública Nacional podían pedir un token para obtener una cuota de uso mayor, y autenticarse con [JWT](https://jwt.io/). El token **no es obligatorio**: la API responde a pedidos sin autenticación.

:::caution[A validar]
En las pruebas del 25/09/2026 contra la v2.1, el gateway respondió `200` tanto a un token inválido como al token de ejemplo de esta página, y los encabezados `x-ratelimit-*` mostraron las mismas cuotas que sin token (10.000 pedidos por día, 40 por minuto). No pudimos confirmar si hoy un token válido cambia la cuota. Antes de pedir uno, consultá a [datosargentina@jefatura.gob.ar](mailto:datosargentina@jefatura.gob.ar).
:::

Para generar un token JWT necesitás dos elementos: una *key* y un *secret* generados para usar con la API. Con ellos podés generar el token, por ejemplo, con Python o Node.js. Los ejemplos usan estos valores de demostración:

- `key = YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk`
- `secret = dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq`

El algoritmo de firma es HMAC-SHA256 (`HS256`).

## Python

Con la librería [`pyjwt`](https://github.com/jpadilla/pyjwt) (versión 2 o posterior, donde `jwt.encode()` devuelve directamente un `str`):

```bash
pip install pyjwt
```

```python
>>> import jwt
>>> key = 'YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk'
>>> secret = 'dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq'
>>> token = jwt.encode({'iss': key}, secret, algorithm='HS256')
>>> token
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZWE5rYzJSaGMyUm1ZWE5rWm1GelptUmhjMlJtWVhOayJ9.P4leoe9q_H3lmIlnpZuVFSt7ORgLhLfQ3JN_3FMexSo'
```

Mandá el token en el encabezado `Authorization`, por ejemplo con [`requests`](https://requests.readthedocs.io/):

```python
>>> import requests
>>> headers = {'Authorization': f'Bearer {token}'}
>>> resp = requests.get('https://apis.datos.gob.ar/georef/api/v2.1/provincias', headers=headers)
>>> resp.json()
{
    'cantidad': 24,
    'provincias': [
        { ... }
    ],
    ...
}
```

## Node.js

Con la librería [`jsonwebtoken`](https://github.com/auth0/node-jsonwebtoken):

```bash
npm install jsonwebtoken
```

```javascript
> const jwt = require('jsonwebtoken')
> const payload = { iss: 'YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk' }
> const secret = 'dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq'
> const token = jwt.sign(payload, secret, { noTimestamp: true })
> token
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZWE5rYzJSaGMyUm1ZWE5rWm1GelptUmhjMlJtWVhOayJ9.P4leoe9q_H3lmIlnpZuVFSt7ORgLhLfQ3JN_3FMexSo'
```

Y lo mandás en el encabezado `Authorization`:

```javascript
> const resp = await fetch('https://apis.datos.gob.ar/georef/api/v2.1/provincias', {
    headers: { Authorization: `Bearer ${token}` }
  })
> await resp.json()
```
