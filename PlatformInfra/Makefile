.PHONY: test setup clean clean-pyc clean-test run

export FLASK_APP = platforminfra

setup:
	/root/.pyenv/shims/pip install -e .

clean: clean-pyc clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	@echo "Not implemented yet"

documents:
	echo "Removing old Docs and regenerating"
	rm -rf ./docs/*
	pdoc --html-dir ./docs --html --all-submodules platforminfra

test:
	python setup.py test

run:
	flask run -h 127.0.0.1

run-dev:
	flask run --with-threads

run-debug:
	FLASK_DEBUG=1 flask run

