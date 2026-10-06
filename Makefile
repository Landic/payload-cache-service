.PHONY: test run

test:
	python -m pytest

run:
	uvicorn app.main:app --reload
