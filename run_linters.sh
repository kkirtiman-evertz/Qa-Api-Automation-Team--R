#!/bin/bash -xe

echo "Run linters and validators from script"
export VIRTUALENV_PIP=21.3.1
pipenv sync --dev --pre
pipenv run prettier . -c
pipenv run bandit -r .
pipenv run black --check .
pipenv run pylint ./tests
pipenv run isort --profile black . --check --diff
