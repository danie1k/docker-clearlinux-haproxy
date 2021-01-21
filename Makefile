
black-fix:
	@black --target-version py37 --line-length 120 ./python/

isort-fix:
	@isort ./python/

black-check:
	@black --version
	@black --check --target-version py37 --line-length 120 ./python/

flake8:
	@flake8 --version
	@flake8 ./python/

mypy:
	@mypy --version
	@mypy ./python/

pylint:
	@pylint --version
	@pylint ./python/

pytest:
	@pytest --version
	@pytest ./python/

yamllint:
	@yamllint --version
	@yamllint --strict .

fix-all: black-fix isort-fix
lint-all: black-check flake8 mypy pylint yamllint
