
fix-linter-issues:
	uv run ruff check --fix app lambdas && \
	uv run ruff format app lambdas

run-type-checker:
	uv run mypy app lambdas --ignore-missing-imports
