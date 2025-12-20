up:
	docker compose -f compose.infra.yaml up -d --build;
	docker compose -f auth/compose.yaml up -d --build;
	docker compose -f notifications/compose.yaml up -d --build;
	docker compose -f payments/compose.yaml up -d --build;
	docker compose -f feedback/compose.yaml up -d --build;

migrate-all:
	cd auth && make migrate
	cd payments && make migrate
	cd feedback && make migrate
