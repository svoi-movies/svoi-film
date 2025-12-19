up:
	docker compose \
		-f subscribes/compose.yaml \
		-f compose.infra.yaml \
		up -d