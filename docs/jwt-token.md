# Tokens JWT

Para utilizar la API de Georef, es necesario autenticarse utilizando tokens [JWT](https://jwt.io/). Para generar un token JWT, se requieren dos elementos: una *key* y un *secret* generados para el uso con la API.

Una vez obtenidos ambos elementos, se puede generar un token JWT utilizando, por ejemplo, Python. A continuación, se muestra un ejemplo utilizando los siguientes valores demostrativos:

- `key = YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk`
- `secret = dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq`

Utilizando la librería `pyjwt`:

```python
$ pip install pyjwt
$ python

>>> import jwt
>>> key = 'YXNkc2Rhc2RmYXNkZmFzZmRhc2RmYXNk'
>>> message = { 'iss': key }
>>> secret = 'dnVvODY4Yzc2bzhzNzZqOG83czY4b2Nq'
>>> token_bytes = jwt.encode(message, secret, algorithm='HS256')
>>> token = token_bytes.decode()
>>> token
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZWE5rYzJSaGMyUm1ZWE5rWm1GelptUmhjMlJtWVhOayJ9.P4leoe9q_H3lmIlnpZuVFSt7ORgLhLfQ3JN_3FMexSo'
```

Finalmente, para consumir la API de Georef, adjuntar el token generado en las cabeceras HTTP. A continuación, se muestra un ejemplo utilizando la librería [requests](http://docs.python-requests.org/en/master/):

```python
>>> import requests
>>> headers = { 'Authorization': 'Bearer {}'.format(token) }
>>> resp = requests.get('<URL de georef>/api/v1.0/provincias', headers=headers)
>>> resp.json()
{
	'provincias': [
		{ ... }
	]
}
```
