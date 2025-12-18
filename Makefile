up:
	docker compose \
		-f auth/compose.yaml \
		-f compose.infra.yaml \
		up -d