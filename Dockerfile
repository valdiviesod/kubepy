FROM python:3

# Instala las dependencias necesarias
RUN pip install kr8s

# Copia el script de Python y el directorio .kube al contenedor
COPY main.py /app/main.py
COPY .kube /root/.kube

# Establece el directorio de trabajo
WORKDIR /app

CMD ["python", "main.py"]
