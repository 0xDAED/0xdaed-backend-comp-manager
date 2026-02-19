## Run infra
docker compose up -d

## Install deps
poetry install
poetry shell

## Init migrations (first time only)
alembic upgrade head

## Run app
uvicorn app.main:app --reload
# 0xdaed-backend-comp-manager
