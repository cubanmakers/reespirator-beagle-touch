

.PHONY: default clean-docker shell clean test build setup
default: shell

clean-docker:
	docker-compose down -v

shell:
	docker-compose run --rm app

clean:
	docker-compose run --rm app /bin/bash -c "rm -r build dist .pytest_cache src/resPyRator.egg-info || true"

test:
	docker-compose run --rm app python -m pytest tests

build:
	docker-compose run --rm app python setup.py bdist_wheel

setup:
	docker-compose run --rm app /bin/bash -c "apt-get -qqy update && apt-get -qqy install libgl1 && pip install -r requirements-test.txt"
