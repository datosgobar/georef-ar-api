# Instalación de Python 3.6

Para instalar Python 3.6 en entornos GNU/Linux, se puede utilizar la herramienta `pyenv` [disponible en GitHub](https://github.com/pyenv/pyenv). `pyenv` permite al usuario instalar cualquier versión de Python existente, e incluso tener varias versiones instaladas simultáneamente.

A continuación, se detallan los pasos necesarios para instalar Python 3.6. Los mismos fueron creados utilizando Ubuntu 16.04.

## 1. Descargar `pyenv`
Clonar el repositorio de `pyenv` en el directorio `~/.pyenv`:
```bash
$ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
```

## 2. Agregar configuración de `pyenv` a `~/.bashrc`
```bash
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
$ echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc
```

## 3. Activar la nueva configuración
```bash
$ source ~/.bashrc
```

## 4. Instalar dependencias para compilar Python
```bash
$ sudo apt install make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
```

## 5. Descargar, compilar e instalar Python 3.6
```bash
$ pyenv install 3.6.5
```

## 6. Activar Python 3.6
Una vez instalado Python 3.6, se debe activar su uso. `pyenv` permite establecer versiones de Python por directorio: de esta forma, es posible clonar el repositorio `georef-ar-api` en una ubicación, y activar el uso de Python 3.6 en la misma:
```bash
$ git clone https://github.com/datosgobar/georef-ar-api.git
$ cd georef-ar-api
$ pyenv version 3.6.5 # activar el uso de Python 3.6
$ python --version    # el comando 'python' ahora utiliza Python 3.6, en este directorio
Python 3.6.5
$ pip --version       # también se instala 'pip' automáticamente
pip 9.0.1 (python 3.6.5)
```
Notar que `pyenv` crea un archivo llamado `.python-version`, donde se especifica la versión de Python que debería ser utilizada en el directorio.
