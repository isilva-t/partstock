.PHONY: venv out upd up

upd: 
	docker compose -f ./srcs/docker-compose.yml --env-file ./srcs/.env up -d --build

up: 
	docker compose -f ./srcs/docker-compose.yml --env-file ./srcs/.env up  --build

clean: 
	docker-compose -f ./srcs/docker-compose.yml down

re: clean upd

venv:
	@echo 'use' 
	@echo 'source venv/bin/activate'

out:
	./out.sh
