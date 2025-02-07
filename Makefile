.ONESHELL:
.DEFAULT_GOAL := help
SHELL := /bin/bash

# underscore separated; aka sdist and whl names
# https://blogs.gentoo.org/mgorny/2023/02/09/the-inconsistencies-around-python-package-naming-and-the-new-policy/
APP_NAME := kenobi

define NORMALIZE_APP_NAME
try:
    from importlib import metadata
except ImportError:
    v = '$(APP_NAME)'.replace('_', "-").replace('.', "-")
    print(v)
else:
    print(metadata.metadata('$(APP_NAME)')['Name']))
endef

#virtual environment. If 0 issue warning
#Not activated:0
#activated: 1
ifeq ($(VIRTUAL_ENV),)
$(warning virtualenv not activated)
is_venv =
else
is_venv = 1
VENV_BIN := $(VIRTUAL_ENV)/bin
VENV_BIN_PYTHON := python3
PY_X_Y := $(shell $(VENV_BIN_PYTHON) -c 'import platform; t_ver = platform.python_version_tuple(); print(".".join(t_ver[:2]));')
endif

ifeq ($(is_venv),1)
  # Package name is hyphen delimited
  PACKAGE_NAME ?= $(shell $(VENV_BIN_PYTHON) -c "$(NORMALIZE_APP_NAME)")
  VENV_PACKAGES ?= $(shell $(VENV_BIN_PYTHON) -m pip list --disable-pip-version-check --no-input | /bin/awk '{print $$1}')
  IS_PACKAGE ?= $(findstring $(1),$(VENV_PACKAGES))

  is_wheel ?= $(call IS_PACKAGE,wheel)
  is_piptools ?= $(call IS_PACKAGE,pip-tools)

  find_whl = $(shell [[ -z "$(3)" ]] && extention=".whl" || extention="$(3)"; [[ -z "$(2)" ]] && srcdir="dist" || srcdir="$(2)/dist"; [[ -z "$(1)" ]] && whl=$$(ls $$srcdir/$(APP_NAME)*.whl  --format="single-column") || whl=$$(ls $$srcdir/$(1)*.whl --format="single-column"); echo $${whl##*/})
endif

##@ Helpers

# https://www.thapaliya.com/en/writings/well-documented-makefiles/
.PHONY: help
help:					## (Default) Display this help -- Always up to date
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)


##@ GNU Make standard targets

.PHONY: build
build:					## Make the source distribution
	@python -m build

.PHONY: install
install: override usage := make [force=1]
install: override check_web := Install failed. Possible cause no web connection
install: private force_text = $(if $(force),"--force-reinstall")
install:				## Installs *as a package*, not *with the ui* -- make [force=1] [debug=1] install
ifeq ($(is_venv),1)
  ifeq ($(is_wheel), wheel)
	@if [[  "$$?" -eq 0 ]]; then

	whl=$(call find_whl,$(APP_NAME),,) #1: PYPI package name (hyphens). 2 folder/app name (APP_NAME;underscores). 3 file extension
	echo $(whl)
	$(VENV_BIN_PYTHON) -m pip install --disable-pip-version-check --no-color --log="/tmp/$(APP_NAME)_install_prod.log" $(force_text) "dist/$$whl"

	fi

  endif
endif

.PHONY: install-force
install-force: force := 1
install-force: install	## Force install even if exact same version

# --cov-report=xml
# Dependencies: pytest, pytest-cov, pytest-regressions
# make [v=1] check
# $(VENV_BIN)/pytest --showlocals --cov=wreck --cov-report=term-missing --cov-config=pyproject.toml $(verbose_text) tests
.PHONY: check
check: private verbose_text = $(if $(v),"--verbose")
check:					## Run tests, generate coverage reports -- make [v=1] check
ifeq ($(is_venv),1)
	-@$(VENV_BIN_PYTHON) -m coverage erase
	$(VENV_BIN_PYTHON) -m coverage run --parallel -m pytest --showlocals $(verbose_text) -m "not slow" tests
	$(VENV_BIN_PYTHON) -m coverage combine
	$(VENV_BIN_PYTHON) -m coverage report --fail-under=88
endif

.PHONY: distclean
distclean:				## Clean build files
	@rm -rf dist/ build/ || :;

# assumes already installed: pyenv and shims
# .rst2html5/ needs to exist, but need not be an actual venv
# .doc requires py310 cuz Sphinx
# .tox contains all supported pyenv versions
.PHONY: configure-pyenv
configure-pyenv:			## Configure pyenv .python-version files
	@which pyenv &>/dev/null
	if [[ "$?" -eq 0 ]]; then

	mkdir -p .venv || :;
	pyenv version-name > .venv/.python-version
	# mkdir .doc || :;
	# echo "3.10.14\n" > .doc/.python-version
	mkdir -p .tox || :;
	pyenv versions --bare > .tox/.python-version
	# mkdir .rst2html5 || :;

	fi
