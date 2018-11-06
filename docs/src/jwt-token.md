# Tokens JWT

Si pertenecés a un organismo de la Administración Pública Nacional y querés incrementar la cuota de uso de la API de Georef, podés pedir un token y autenticarte utilizando [JWT](https://jwt.io/).

Para generar un token JWT, se requieren dos elementos: una *key* y un *secret* generados para el uso con la API.

Una vez obtenidos ambos elementos, se puede generar un token JWT utilizando, por ejemplo, Python o Node.js. A continuación, se muestran ejemplos utilizando los siguientes valores demostrativos:

- `key = YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk`
- `secret = dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq`

El algoritmo de autentificación de mensajes con *hash* utilizado es HMAC-SHA256 (`HS256`).

## Python

Utilizando la librería [`pyjwt`](https://github.com/jpadilla/pyjwt):

```bash
$ pip install pyjwt
$ python
```
```python
>>> import jwt
>>> key = 'YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk'
>>> message = { 'iss': key }
>>> secret = 'dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq'
>>> token_bytes = jwt.encode(message, secret, algorithm='HS256')
>>> token = token_bytes.decode()
>>> token
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZWE5rYzJSaGMyUm1ZWE5rWm1GelptUmhjMlJtWVhOayJ9.P4leoe9q_H3lmIlnpZuVFSt7ORgLhLfQ3JN_3FMexSo'
```

Finalmente, para consumir la API de Georef, adjuntar el token generado en las cabeceras HTTP. A continuación, se muestra un ejemplo utilizando la librería [`requests`](http://docs.python-requests.org/en/master/):

```python
>>> import requests
>>> headers = { 'Authorization': 'Bearer {}'.format(token) }
>>> resp = requests.get('https://apis.datos.gob.ar/georef/api/provincias', headers=headers)
>>> resp.json()
{
	'provincias': [
		{ ... }
	]
}
```

## Node.js

Utilizando la librería [`jswonwebtoken`](https://github.com/auth0/node-jsonwebtoken):

```bash
$ npm install jsonwebtoken
$ node
```
```javascript
> var jwt = require('jsonwebtoken')
> var payload = { 'iss': 'YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk' }
> var secret = 'dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq'
> var token = jwt.sign(payload, secret, { 'noTimestamp': true })
> token
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZWE5rYzJSaGMyUm1ZWE5rWm1GelptUmhjMlJtWVhOayJ9.P4leoe9q_H3lmIlnpZuVFSt7ORgLhLfQ3JN_3FMexSo'
```

Finalmente, para consumir la API de Georef, adjuntar el token generado en las cabeceras HTTP:

```javascript
> var http = require('http')
> http.get({
	'hostname': 'apis.datos.gob.ar',
	'path': '/georef/api/provincias',
	'headers': {
		'authorization': 'Bearer ' + token
	  }
  }, function(response) {
	...
  })
```
