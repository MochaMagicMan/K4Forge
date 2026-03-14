.PHONY: verify test test-fast lint scaffold clean theory-prove theory-mine theory-all

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

# Theory mining — proof chain
theory-prove:
	python -m k4_theory --prove

# Theory mining — symmetry miner
theory-mine:
	python -m k4_theory --mine

# Theory mining — all phases (prove + mine + discover)
theory-all:
	python -m k4_theory

# Lint
lint:
	ruff check k4_explorer/ k4_artifacts/ k4_viz/ k4_cli/ k4_theory/

# Run the BASIC-BZ preset and save artifact
run-basic:
	k4 run basic-bz --output runs/dev_basic_bz

# Clean generated artifacts (not example)
clean:
	rm -rf runs/dev_*
	find . -name __pycache__ -type d -exec rm -rf {} +
