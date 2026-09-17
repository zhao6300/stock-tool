.PHONY: help test clean

help:
	@echo "make test - run tests"
	@echo "make clean - remove caches"

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
