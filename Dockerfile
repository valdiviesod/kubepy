FROM python:3

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de la aplicación en el contenedor
COPY . .

RUN pip install kr8s

CMD ["python", "main.py"]
