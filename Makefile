.PHONY: venv out upd up clean

upd: 
	docker compose -f ./srcs/docker-compose.yml --env-file ./srcs/.env up -d --build

up: 
	docker compose -f ./srcs/docker-compose.yml --env-file ./srcs/.env up  --build

clean: 
	docker compose -f ./srcs/docker-compose.yml down

re: clean upd

venv:
	@echo 'use' 
	@echo 'source venv/bin/activate'

init-db:
	docker exec partstock-backend python -m app.scripts.init_db

makes-models:
	docker exec partstock-backend python -m app.scripts.makes_models

example:
	docker exec partstock-backend python -m app.scripts.populate_examples

exampleclean:
	docker exec partstock-backend python -m app.scripts.populate_examples clear

out:
	./out.sh
