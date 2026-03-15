.PHONY: clean-pyc clean-build docs clean help install-dev pr

define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@echo "Available commands:"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test artifacts"
	@echo "clean - run clean-build, clean-pyc, and clean-test"
	@echo "install-dev - install development requirements"
	@echo "fix - fix formatting & linting issues with ruff"
	@echo "lint - run pre-commit hooks on all files"
	@echo "linux-docs - generate Sphinx HTML documentation, including API docs"
	@echo "typecheck - run pyrefly type checking"
	@echo "test - run tests quickly with the default Python"
	@echo "docs-ci - generate docs for CI"
	@echo "docs - generate docs and open in browser"
	@echo "dist - build package and show contents"
	@echo "pr - run clean, lint, and test (everything needed before creating a PR)"


clean: clean-build clean-pyc clean-test ## remove all build, test, and Python artifacts

install-dev: ## install package in editable mode with dev deps and pre-commit (uses uv)
	uv pip install --upgrade pip
	uv pip install --group dev -e .
	pre-commit install

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -fr {} +
	find . -name '*.pyo' -exec rm -fr {} +
	find . -name '*~' -exec rm -fr {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test artifacts
	rm -fr .tox/
	rm -fr .mypy_cache
	rm -fr .ruff_cache
	rm -fr .pytest_cache/


lint: ## check style with pre-commit
	@pre-commit run --all-files --show-diff-on-failure || ( \
		echo "\n\n\n * pre-commit should have fixed the errors above. Running again to make sure everything is good..." \
		&& pre-commit run --all-files --show-diff-on-failure \
	)

fix:
	python -m ruff check --fix

typecheck: ## run type checking with pyrefly
	pyrefly check dag/

test: ## run tests quickly with the default Python
	python -m pytest tests

linux-docs: ## generate Sphinx HTML documentation, including API docs
	rm -fr docs/dag.rst
	rm -fr docs/modules.rst
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

docs:
	rm -f docs/dag.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ dag
	$(MAKE) -C docs clean
	$(MAKE) -C docs html SPHINXOPTS="-W"

docs-ci: ## generate docs for CI
	python newsfragments/validate_files.py
	rm -f docs/dag.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ dag
	$(MAKE) -C docs clean
	$(MAKE) -C docs html SPHINXOPTS="-W"

dist: clean
	python -m build
	ls -l dist

pr: clean fix lint typecheck test
	@echo "PR preparation complete! All checks passed."

# release commands

package-test: clean
	python -m build
	python scripts/release/test_package.py

notes: check-bump validate-newsfragments
	# Let UPCOMING_VERSION be the version that is used for the current bump
	$(eval UPCOMING_VERSION=$(shell bump-my-version bump --dry-run $(bump) -v | awk -F"'" '/New version will be / {print $$2}'))
	# Now generate the release notes to have them included in the release commit
	towncrier build --yes --version $(UPCOMING_VERSION)
	# Before we bump the version, make sure that the towncrier-generated docs will build
	make build-docs
	git commit -m "Compile release notes for v$(UPCOMING_VERSION)"

release: check-bump check-git clean
	# verify that notes command ran correctly
	./newsfragments/validate_files.py is-empty
	CURRENT_SIGN_SETTING=$(git config commit.gpgSign)
	git config commit.gpgSign true
	bump-my-version bump $(bump)
	python -m build
	git config commit.gpgSign "$(CURRENT_SIGN_SETTING)"
	git push upstream && git push upstream --tags
	twine upload dist/*

# release helpers

check-bump:
ifndef bump
	$(error bump must be set, typically: major, minor, patch, or devnum)
endif

validate-newsfragments:
	python ./newsfragments/validate_files.py
	towncrier build --draft --version preview

check-git:
	# require that upstream is configured for libp2p/py-libp2p
	@if ! git remote -v | grep "upstream[[:space:]]git@github.com:libp2p/py-libp2p.git (push)\|upstream[[:space:]]https://github.com/libp2p/py-libp2p (push)"; then \
		echo "Error: You must have a remote named 'upstream' that points to 'py-libp2p'"; \
		exit 1; \
	fi

build-docs:
	sphinx-apidoc -o docs/ . "*conftest*" tests/
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
