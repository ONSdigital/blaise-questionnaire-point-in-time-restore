.PHONY: lint lint-fix typecheck deptry vulture test run

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check --fix .
	poetry run ruff format .

typecheck:
	poetry run pyright

deptry:
	poetry run deptry .

vulture:
	poetry run vulture .

test:
	poetry run pytest

run:
	@questionnaire="$(word 2,$(MAKECMDGOALS))"; \
	timestamp="$$(printf "%s" "$(wordlist 3,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))")"; \
	if [ -z "$$questionnaire" ] || [ -z "$$timestamp" ]; then \
		echo "Usage: make run <questionnaire_name> <YYYY-MM-DD HH:MM:SS>"; \
		exit 2; \
	fi; \
	bash scripts/run_restore.sh "$$questionnaire" "$$timestamp"

%:
	@:
