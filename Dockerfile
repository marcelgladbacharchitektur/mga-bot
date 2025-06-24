# Verwende ein offizielles, schlankes Python-Image
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere System-Dependencies für Google API Client
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die Abhängigkeiten-Datei und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installiere python-dotenv falls noch nicht in requirements.txt
RUN pip install python-dotenv

# Kopiere den gesamten Quellcode in das Arbeitsverzeichnis
COPY ./src ./src

# Stelle sicher, dass die .env Datei geladen wird
ENV PYTHONUNBUFFERED=1

# Definiere den Befehl, der beim Start des Containers ausgeführt wird
CMD ["python", "src/telegram_agent_google.py"]