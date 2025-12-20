ENV_PREFIX = APP_DOTENV_FILE_PATH=./.dev/.env APP_SECRET_DIR_PATH=./.dev/secrets

generate-schema:
	$(ENV_PREFIX) uv run python -m commons.scripts.generate_openapi_schema "streaming.api:create_app" --factory

generate-client: generate-schema
	openapi-generator-cli generate -g python -o client -i openapi.json -c openapi-generator-config.yaml

docker-dev:
	docker compose -f compose.yaml -f ../compose.infra.yaml up

docker-dev-build:
	docker compose -f compose.yaml -f ../compose.infra.yaml up --build


api:
	$(ENV_PREFIX) uv run uvicorn --reload --workers 1 --factory streaming.api:create_app

worker:
	$(ENV_PREFIX) uv run python -m streaming.worker

migrate:
	$(ENV_PREFIX) uv run alembic upgrade head

generate-migration:
	$(ENV_PREFIX) uv run alembic revision --autogenerate -m "$(MESSAGE)"