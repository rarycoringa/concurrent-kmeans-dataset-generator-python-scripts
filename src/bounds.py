import argparse
import csv


def compute_bounds(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []

        mins: dict[str, float | str | None] = {col: None for col in fields}
        maxs: dict[str, float | str | None] = {col: None for col in fields}
        numeric: dict[str, bool] = {col: True for col in fields}

        for row in reader:
            for col in fields:
                val = row[col]
                if val == "":
                    continue

                if numeric[col]:
                    try:
                        fval = float(val)
                        if mins[col] is None or fval < mins[col]:  # type: ignore[operator]
                            mins[col] = fval
                        if maxs[col] is None or fval > maxs[col]:  # type: ignore[operator]
                            maxs[col] = fval
                        continue
                    except ValueError:
                        numeric[col] = False

                # Lexicographic fallback for non-numeric columns
                if mins[col] is None or val < mins[col]:  # type: ignore[operator]
                    mins[col] = val
                if maxs[col] is None or val > maxs[col]:  # type: ignore[operator]
                    maxs[col] = val

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["column", "min", "max"])
        for col in fields:
            writer.writerow([col, mins[col], maxs[col]])

    print(f"Bounds written to {output_path} ({len(fields)} columns)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute per-column min/max from the generated dataset")
    parser.add_argument("--input", default="data/consumption.csv", help="Input CSV path")
    parser.add_argument("--output", default="data/mins_and_maxs.csv", help="Output bounds CSV path")
    args = parser.parse_args()

    compute_bounds(args.input, args.output)


if __name__ == "__main__":
    main()
