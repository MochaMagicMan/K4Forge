.PHONY: verify test test-fast lint scaffold clean

# Run the 182-check frozen core verification
verify:
	python -m k4_frozen.verify_all

# Run all tests
test:
	pytest tests/ -v

# Run fast tests only (skip SymPy gates)
test-fast:
	pytest tests/ -v -m "not gates"

# Run vertical slice only
test-vertical:
	pytest tests/test_vertical_slice.py -v

# Import rule enforcement
test-imports:
	pytest tests/test_imports.py -v

# Lint
lint:
	ruff check k4_explorer/ k4_artifacts/ k4_viz/ k4_cli/

# Run the BASIC-BZ preset and save artifact
run-basic:
	k4 run basic-bz --output runs/dev_basic_bz

# Clean generated artifacts (not example)
clean:
	rm -rf runs/dev_*
	find . -name __pycache__ -type d -exec rm -rf {} +
