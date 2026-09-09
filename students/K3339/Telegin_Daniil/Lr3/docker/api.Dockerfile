FROM python:3.11-slim

WORKDIR /app

COPY students/K3339/Telegin_Daniil/Lr1/requirements.txt /tmp/requirements-lr1.txt
COPY students/K3339/Telegin_Daniil/Lr3/requirements-api.txt /tmp/requirements-api.txt
RUN pip install --no-cache-dir -r /tmp/requirements-lr1.txt -r /tmp/requirements-api.txt

COPY students/K3339/Telegin_Daniil/Lr1/alembic.ini ./alembic.ini
COPY students/K3339/Telegin_Daniil/Lr1/migrations ./migrations
COPY students/K3339/Telegin_Daniil/Lr1/app ./app
COPY students/K3339/Telegin_Daniil/Lr3/lr3_api.py ./lr3_api.py

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn lr3_api:app --host 0.0.0.0 --port 8000"]
