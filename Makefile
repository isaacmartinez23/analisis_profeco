# Pipeline de precios PROFECO QQP.
# Cada objetivo delega en `python -m src.cli`, que también funciona en Windows sin make.
# Uso: make pipeline            (datos completos en data/raw)
#      make pipeline MUESTRA=1  (muestra versionada en data/sample)

PYTHON ?= python
MUESTRA ?=
CLI = $(PYTHON) -m src.cli $(if $(MUESTRA),--muestra,)

.PHONY: setup inspect ingest quality normalize dbt-run dbt-test quality-marts test publish pipeline sample profile clean

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(CLI) setup

inspect:
	$(CLI) inspect

ingest:
	$(CLI) ingest

quality:
	$(CLI) quality

normalize:
	$(CLI) normalize

dbt-run:
	$(CLI) dbt-run

dbt-test:
	$(CLI) dbt-test

quality-marts:
	$(CLI) quality-marts

test:
	$(CLI) test

publish:
	$(CLI) publish

pipeline:
	$(CLI) pipeline

sample:
	$(CLI) sample

profile:
	$(CLI) profile

clean:
	$(CLI) clean
