up:
	docker compose \
		-f template/compose.yaml \
		-f compose.infra.yaml \
		up -d