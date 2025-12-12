up:
	docker compose \
		-f docker-compose.yaml
		-f template/docker-compose.template.yaml
		up

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

sync-all:
	uv sync --all-groups 