.DEFAULT_GOAL := build

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: setup build build-no-preview test check install install-dry-run uninstall package vscode cvd doctor clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

build:
	"$(PYTHON)" green_eye.py build

build-no-preview:
	"$(PYTHON)" green_eye.py build --no-preview

test:
	"$(PYTHON)" green_eye.py test

check:
	"$(PYTHON)" green_eye.py check

install:
	"$(PYTHON)" green_eye.py install

install-dry-run:
	"$(PYTHON)" green_eye.py install --dry-run

uninstall:
	"$(PYTHON)" green_eye.py install --uninstall

package:
	"$(PYTHON)" green_eye.py package

vscode:
	"$(PYTHON)" green_eye.py vscode

cvd:
	"$(PYTHON)" green_eye.py cvd

doctor:
	"$(PYTHON)" green_eye.py doctor

clean:
	"$(PYTHON)" green_eye.py clean
