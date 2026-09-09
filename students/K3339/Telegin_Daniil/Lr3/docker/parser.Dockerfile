FROM python:3.11-slim

WORKDIR /app

COPY students/K3339/Telegin_Daniil/Lr3/requirements-parser.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY students/K3339/Telegin_Daniil/Lr3/services ./services

EXPOSE 8001
CMD ["uvicorn", "services.parser.main:app", "--host", "0.0.0.0", "--port", "8001"]
