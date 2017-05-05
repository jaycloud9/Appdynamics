.PHONY: test setup clean clean-pyc clean-test run

export FLASK_APP = platforminfra

setup:
	pip install -e .

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
	rm -f ./docs/source/*.rst
	sphinx-apidoc -f -e -M --implicit-namespaces -o docs/source/ tests
	sphinx-apidoc -f -e -M --implicit-namespaces -o docs/source/ platforminfra
	sphinx-build -c docs/source/ docs/source/ docs/build/


e2etest:
	python -W ignore setup.py test -s tests.e2etest

test:
	python -W ignore setup.py test -s tests.unit

run:
	flask run -h 127.0.0.1

run-dev:
	flask run --with-threads

run-debug:
	FLASK_DEBUG=1 flask run
