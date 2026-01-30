EXAMPLE ?= $(firstword $(filter-out shell,$(MAKECMDGOALS)))

.PHONY: install shell publish test test-verbose clean
.PHONY: product_catalog recipes bookmarks knowledge_graph org_chart products

install:
	uv sync --dev

shell:
	@example="$(EXAMPLE)"; \
	if [ -z "$$example" ]; then \
		uv run python -m loopy.shell; \
	else \
		case "$$example" in \
			products) example="product_catalog" ;; \
		esac; \
		LOOPY_EXAMPLE="$$example" uv run python -c "import os, examples; from loopy.shell import repl; name=os.environ['LOOPY_EXAMPLE']; repl(getattr(examples, name)())"; \
	fi

test:
	uv run pytest

test-verbose:
	uv run pytest -vv

publish:
	rm -rf dist
	uv build
	uv run twine upload --repository pypi dist/loopy_fs-*

clean:
	rm -rf dist
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +

product_catalog recipes bookmarks knowledge_graph org_chart products:
	@:
