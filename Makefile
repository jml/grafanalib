.DEFAULT_GOAL := help
.PHONY: check coverage help lint test type-check

lint:  ## Run the lint checks
	pipenv run pre-commit run --all-files

type-check:  ## Check the code for type safety
	pipenv run mypy src tests

test:  ## Run the tests without coverage
	pipenv run pytest tests

coverage: .coveragerc $(shell find src tests -name '*.py')
	pipenv run coverage run -m pytest -q tests

coverage-check: coverage
	pipenv run coverage report --fail-under=80 --show-missing

check: lint type-check coverage-check  ## All the checks run in CI

help:  ## List Makefile targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
