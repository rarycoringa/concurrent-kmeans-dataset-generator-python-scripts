# This script was generated with the assistance of GitHub Copilot, using model claude-sonnet-4.6.
# It produces a synthetic CSV dataset for K-means clustering experiments on UK home energy consumption.
# The data and consumption logic are entirely fictional and intended for educational/research purposes only.

import argparse
import csv
import uuid
from dataclasses import dataclass
import numpy as np

np.random.seed(42)

UK_CITIES = [
    ("London",       51.5074, -0.1278),
    ("Manchester",   53.4808, -2.2426),
    ("Birmingham",   52.4862, -1.8904),
    ("Leeds",        53.8008, -1.5491),
    ("Glasgow",      55.8642, -4.2518),
    ("Sheffield",    53.3811, -1.4701),
    ("Edinburgh",    55.9533, -3.1883),
    ("Liverpool",    53.4084, -2.9916),
    ("Bristol",      51.4545, -2.5879),
    ("Cardiff",      51.4816, -3.1791),
    ("Leicester",    52.6369, -1.1398),
    ("Coventry",     52.4068, -1.5197),
    ("Nottingham",   52.9548, -1.1581),
    ("Newcastle",    54.9783, -1.6178),
    ("Belfast",      54.5973, -5.9301),
]

# Base monthly kWh per unit for each appliance
APPLIANCE_BASE_KWH = {
    "refrigerator":    35,
    "freezer":         25,
    "washing_machine": 18,
    "dryer":           25,
    "dishwasher":      20,
    "oven":            20,
    "microwave":        4,
    "tv":              15,
    "computer":        22,
    "heat_pump":      300,
    "air_conditioner": 80,
    "water_heater":   120,
    "ev_charger":     280,
    "lighting_indoor": 30,
    "lighting_outdoor":10,
}


@dataclass
class RunningStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float = float("inf")
    maximum: float = float("-inf")

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)

    @property
    def std(self) -> float:
        if self.count < 2:
            return 0.0
        return float(np.sqrt(self.m2 / (self.count - 1)))


def print_stats(label: str, stats: RunningStats) -> None:
    if stats.count == 0:
        return

    print(
        f"{label}: count={stats.count}, mean={stats.mean:.2f}, std={stats.std:.2f}, "
        f"min={stats.minimum:.2f}, max={stats.maximum:.2f}"
    )


def noisy(base: float, noise_pct: float = 0.12) -> float:
    return max(0.0, base * (1 + np.random.normal(0, noise_pct)))


def generate_row(index: int) -> dict:
    sensor_id = f"S-{uuid.uuid4().hex[:8].upper()}"

    city, lat, lon = UK_CITIES[np.random.randint(len(UK_CITIES))]
    lat = round(lat + np.random.uniform(-0.15, 0.15), 4)
    lon = round(lon + np.random.uniform(-0.15, 0.15), 4)

    # --- Home profile ---
    num_bedrooms = int(np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.25, 0.35, 0.20, 0.10]))
    base_size = {1: 45, 2: 70, 3: 95, 4: 130, 5: 175}[num_bedrooms]
    home_size_m2 = round(max(30.0, base_size + np.random.normal(0, 10)), 1)
    size_factor = home_size_m2 / 95  # normalised to 3-bed average

    # Garden and garage probability grows with home size
    has_garden = int(np.random.random() < min(0.95, 0.25 + 0.15 * num_bedrooms))
    has_garage = int(np.random.random() < min(0.90, 0.08 + 0.13 * num_bedrooms))

    # --- People profile ---
    num_residents = int(np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.30, 0.20, 0.20, 0.10, 0.05]))
    num_children  = int(np.random.randint(0, min(num_residents, 4)))
    num_adults    = num_residents - num_children
    people_factor = num_residents / 2.5  # normalised to avg UK household

    # --- Appliance quantities ---
    qty_refrigerator     = 1 if num_bedrooms <= 3 else int(np.random.choice([1, 2], p=[0.70, 0.30]))
    qty_freezer          = int(np.random.choice([0, 1], p=[0.40, 0.60]) if num_bedrooms >= 2
                               else np.random.choice([0, 1], p=[0.70, 0.30]))
    qty_washing_machine  = 1 if num_bedrooms <= 4 else int(np.random.choice([1, 2], p=[0.80, 0.20]))
    qty_dryer            = int(np.random.choice([0, 1], p=[0.35, 0.65]) if num_residents >= 2
                               else np.random.choice([0, 1], p=[0.60, 0.40]))
    qty_dishwasher       = int(np.random.choice([0, 1], p=[0.30, 0.70]) if num_residents >= 3
                               else np.random.choice([0, 1], p=[0.65, 0.35]))
    qty_oven             = 1 if num_bedrooms <= 4 else int(np.random.choice([1, 2], p=[0.90, 0.10]))
    qty_microwave        = int(np.random.choice([0, 1, 2], p=[0.10, 0.75, 0.15]))
    qty_tv               = int(min(num_bedrooms, max(1, np.random.poisson(num_residents * 0.6))))
    qty_computer         = int(max(0, round(num_adults * np.random.uniform(0.5, 1.2))))
    qty_heat_pump        = int(np.random.choice([0, 1], p=[0.65, 0.35]))
    qty_air_conditioner  = int(np.random.choice([0, 1], p=[0.82, 0.18]))
    qty_water_heater     = 1
    qty_ev_charger       = int(np.random.choice([0, 1], p=[0.78, 0.22]))

    # --- Consumption (monthly kWh) ---
    # Fixed appliances: base kWh × qty (+ noise)
    c_refrigerator    = qty_refrigerator    * noisy(APPLIANCE_BASE_KWH["refrigerator"])
    c_freezer         = qty_freezer         * noisy(APPLIANCE_BASE_KWH["freezer"])
    c_microwave       = qty_microwave       * noisy(APPLIANCE_BASE_KWH["microwave"])

    # Usage-driven: scale with people
    c_washing_machine = qty_washing_machine * noisy(APPLIANCE_BASE_KWH["washing_machine"] * people_factor)
    c_dryer           = qty_dryer           * noisy(APPLIANCE_BASE_KWH["dryer"]           * people_factor)
    c_dishwasher      = qty_dishwasher      * noisy(APPLIANCE_BASE_KWH["dishwasher"]      * people_factor)
    c_oven            = qty_oven            * noisy(APPLIANCE_BASE_KWH["oven"]            * people_factor)
    c_water_heater    = qty_water_heater    * noisy(APPLIANCE_BASE_KWH["water_heater"]    * people_factor)

    # Entertainment: scale with qty only
    c_tv              = qty_tv       * noisy(APPLIANCE_BASE_KWH["tv"])
    c_computer        = qty_computer * noisy(APPLIANCE_BASE_KWH["computer"])

    # Space-driven: scale with home size
    c_heat_pump       = qty_heat_pump       * noisy(APPLIANCE_BASE_KWH["heat_pump"]       * size_factor)
    c_air_conditioner = qty_air_conditioner * noisy(APPLIANCE_BASE_KWH["air_conditioner"] * size_factor)

    # EV: fixed base regardless of home
    c_ev_charger      = qty_ev_charger * noisy(APPLIANCE_BASE_KWH["ev_charger"])

    # Lighting: driven by size; garage adds a small overhead
    indoor_base       = APPLIANCE_BASE_KWH["lighting_indoor"] * size_factor + (5 if has_garage else 0)
    c_lighting_indoor  = noisy(indoor_base)
    c_lighting_outdoor = has_garden * noisy(APPLIANCE_BASE_KWH["lighting_outdoor"])

    total = sum([
        c_refrigerator, c_freezer, c_washing_machine, c_dryer,
        c_dishwasher, c_oven, c_microwave, c_tv, c_computer,
        c_heat_pump, c_air_conditioner, c_water_heater, c_ev_charger,
        c_lighting_indoor, c_lighting_outdoor,
    ])

    return {
        "sensor_id":                        sensor_id,
        "city":                             city,
        "latitude":                         lat,
        "longitude":                        lon,
        "home_size_m2":                     home_size_m2,
        "num_bedrooms":                     num_bedrooms,
        "has_garden":                       has_garden,
        "has_garage":                       has_garage,
        "num_residents":                    num_residents,
        "num_adults":                       num_adults,
        "num_children":                     num_children,
        "qty_refrigerator":                 qty_refrigerator,
        "consumption_refrigerator_kwh":     round(c_refrigerator, 2),
        "qty_freezer":                      qty_freezer,
        "consumption_freezer_kwh":          round(c_freezer, 2),
        "qty_washing_machine":              qty_washing_machine,
        "consumption_washing_machine_kwh":  round(c_washing_machine, 2),
        "qty_dryer":                        qty_dryer,
        "consumption_dryer_kwh":            round(c_dryer, 2),
        "qty_dishwasher":                   qty_dishwasher,
        "consumption_dishwasher_kwh":       round(c_dishwasher, 2),
        "qty_oven":                         qty_oven,
        "consumption_oven_kwh":             round(c_oven, 2),
        "qty_microwave":                    qty_microwave,
        "consumption_microwave_kwh":        round(c_microwave, 2),
        "qty_tv":                           qty_tv,
        "consumption_tv_kwh":               round(c_tv, 2),
        "qty_computer":                     qty_computer,
        "consumption_computer_kwh":         round(c_computer, 2),
        "qty_heat_pump":                    qty_heat_pump,
        "consumption_heat_pump_kwh":        round(c_heat_pump, 2),
        "qty_air_conditioner":              qty_air_conditioner,
        "consumption_air_conditioner_kwh":  round(c_air_conditioner, 2),
        "qty_water_heater":                 qty_water_heater,
        "consumption_water_heater_kwh":     round(c_water_heater, 2),
        "qty_ev_charger":                   qty_ev_charger,
        "consumption_ev_charger_kwh":       round(c_ev_charger, 2),
        "consumption_lighting_indoor_kwh":  round(c_lighting_indoor, 2),
        "consumption_lighting_outdoor_kwh": round(c_lighting_outdoor, 2),
        "total_consumption_kwh":            round(total, 2),
    }


def write_dataset(output_path: str, row_count: int, flush_every: int) -> None:
    home_size_stats = RunningStats()
    residents_stats = RunningStats()
    total_consumption_stats = RunningStats()

    with open(output_path, "w", newline="") as csv_file:
        writer = None

        for index in range(row_count):
            row = generate_row(index + 1)

            if writer is None:
                writer = csv.DictWriter(csv_file, fieldnames=list(row.keys()))
                writer.writeheader()

            writer.writerow(row)
            home_size_stats.update(row["home_size_m2"])
            residents_stats.update(row["num_residents"])
            total_consumption_stats.update(row["total_consumption_kwh"])

            if flush_every > 0 and (index + 1) % flush_every == 0:
                csv_file.flush()

    print(f"Generated {row_count} rows -> {output_path}")
    print_stats("home_size_m2", home_size_stats)
    print_stats("num_residents", residents_stats)
    print_stats("total_consumption_kwh", total_consumption_stats)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic UK home energy consumption dataset")
    parser.add_argument("--size", type=int, default=1000, help="Number of rows to generate (default: 1000)")
    parser.add_argument("--output", default="data/consumption.csv", help="Output CSV path")
    parser.add_argument(
        "--flush-every",
        type=int,
        default=100000,
        help="Flush the file buffer every N rows; set 0 to disable explicit flushes",
    )
    args = parser.parse_args()

    if args.size < 0:
        raise ValueError("--size must be non-negative")

    if args.flush_every < 0:
        raise ValueError("--flush-every must be non-negative")

    write_dataset(args.output, args.size, args.flush_every)


if __name__ == "__main__":
    main()
