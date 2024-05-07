# Verwenden Sie ein offizielles Python-Laufzeitbild als Elternbild
FROM python:3.8-slim-buster

# Setzen Sie die Arbeitsumgebung im Container auf /app
WORKDIR /app

# Kopieren Sie die aktuellen Verzeichnisinhalte in das Arbeitsverzeichnis /app im Container
ADD . /app

# Installieren Sie alle benötigten Pakete
RUN pip install --no-cache-dir -r requirements.txt

# Machen Sie den Port 5000 des Containers verfügbar für die Welt außerhalb dieses Containers
EXPOSE 5000

# Führen Sie app.py aus, wenn der Container gestartet wird
CMD ["python", "app.py"]