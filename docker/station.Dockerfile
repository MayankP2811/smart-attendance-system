# Attendance station in mock mode (no fingerprint sensor, LCD or camera needed).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY device ./device
ENTRYPOINT ["python", "-m", "device.main", "--mock"]
