.DEFAULT_GOAL := build

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: setup build test check install install-dry-run uninstall clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

build:
	PYTHON="$(PYTHON)" bash intellij/scripts/build.sh

test:
	"$(PYTHON)" -m unittest discover -s tests -v
	bash intellij/scripts/test_install.sh

check:
	"$(PYTHON)" shared/tools/check_palette.py

install:
	bash intellij/scripts/install.sh

install-dry-run:
	bash intellij/scripts/install.sh --dry-run

uninstall:
	bash intellij/scripts/install.sh --uninstall

clean:
	find intellij/src shared/tools -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.tmp.*' -delete
	find . -type f -name '*.pyc' -delete
