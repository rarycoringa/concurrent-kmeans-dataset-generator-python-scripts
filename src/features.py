import argparse
import csv


def extract_features(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        features = reader.fieldnames or []

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["feature"])
        for feature in features:
            writer.writerow([feature])

    print(f"Features written to {output_path} ({len(features)} features)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract feature names from the generated marketplace orders CSV")
    parser.add_argument("--input", default="data/orders.csv", help="Input CSV path")
    parser.add_argument("--output", default="data/features.csv", help="Output features CSV path")
    args = parser.parse_args()

    extract_features(args.input, args.output)


if __name__ == "__main__":
    main()
