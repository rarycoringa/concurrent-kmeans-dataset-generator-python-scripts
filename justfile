generate size="1000":
    uv run python src/generator.py --size {{size}}

bound:
    uv run python src/bounds.py

feature:
    uv run python src/features.py