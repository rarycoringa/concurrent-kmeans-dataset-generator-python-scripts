import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

RNG = np.random.default_rng(42)

UK_CITIES = [
    ("London", 51.5074, -0.1278),
    ("Manchester", 53.4808, -2.2426),
    ("Birmingham", 52.4862, -1.8904),
    ("Leeds", 53.8008, -1.5491),
    ("Glasgow", 55.8642, -4.2518),
    ("Sheffield", 53.3811, -1.4701),
    ("Edinburgh", 55.9533, -3.1883),
    ("Liverpool", 53.4084, -2.9916),
    ("Bristol", 51.4545, -2.5879),
    ("Cardiff", 51.4816, -3.1791),
    ("Leicester", 52.6369, -1.1398),
    ("Coventry", 52.4068, -1.5197),
    ("Nottingham", 52.9548, -1.1581),
    ("Newcastle", 54.9783, -1.6178),
    ("Belfast", 54.5973, -5.9301),
]

CHANNEL_WEIGHTS = np.array([0.42, 0.58])
PAYMENT_WEIGHTS = np.array([0.64, 0.21, 0.11, 0.04])
ORDER_ARCHETYPE_WEIGHTS = np.array([0.18, 0.23, 0.17, 0.18, 0.24])
ARCHETYPE_CATEGORY_WEIGHTS = np.array(
    [
        [0.55, 0.23, 0.04, 0.08, 0.10],  # grocery-led
        [0.12, 0.52, 0.06, 0.08, 0.22],  # household restock
        [0.02, 0.08, 0.68, 0.05, 0.17],  # electronics-led
        [0.03, 0.07, 0.08, 0.68, 0.14],  # fashion-led
        [0.08, 0.16, 0.19, 0.17, 0.40],  # home mixed
    ]
)
CATEGORY_PRICE_RANGES = {
    "grocery": (2.5, 14.0),
    "household": (5.0, 26.0),
    "electronics": (40.0, 520.0),
    "fashion": (18.0, 130.0),
    "home": (15.0, 220.0),
}
CATEGORY_TAX_RATES = {
    "grocery": 0.03,
    "household": 0.18,
    "electronics": 0.20,
    "fashion": 0.20,
    "home": 0.20,
}


@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    city: str
    latitude: float
    longitude: float
    segment_code: int
    tenure_days: int
    orders_last_90d: int
    is_priority_member: int
    coupon_affinity: float


@dataclass(frozen=True)
class SellerProfile:
    seller_id: str
    city: str
    latitude: float
    longitude: float
    seller_rating: float
    seller_orders_last_30d: int
    fulfilled_by_marketplace_bias: float
    express_bias: float


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


def sample_location() -> tuple[str, float, float]:
    city, latitude, longitude = UK_CITIES[int(RNG.integers(len(UK_CITIES)))]
    return (
        city,
        round(latitude + float(RNG.uniform(-0.18, 0.18)), 4),
        round(longitude + float(RNG.uniform(-0.18, 0.18)), 4),
    )


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat_factor = 111.32
    lon_factor = 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
    lat_delta = (lat1 - lat2) * lat_factor
    lon_delta = (lon1 - lon2) * lon_factor
    return math.sqrt(lat_delta * lat_delta + lon_delta * lon_delta)


def pool_size(row_count: int, minimum: int, maximum: int, divisor: int) -> int:
    if row_count <= 0:
        return minimum
    return max(minimum, min(maximum, row_count // divisor))


def build_customer_pool(count: int) -> list[CustomerProfile]:
    customers: list[CustomerProfile] = []

    for index in range(count):
        city, latitude, longitude = sample_location()
        segment_code = int(RNG.choice([0, 1, 2, 3], p=[0.22, 0.34, 0.29, 0.15]))

        if segment_code == 0:
            tenure_days = int(RNG.integers(1, 90))
            orders_last_90d = int(RNG.integers(0, 4))
            is_priority_member = int(RNG.random() < 0.06)
            coupon_affinity = float(RNG.uniform(0.35, 0.75))
        elif segment_code == 1:
            tenure_days = int(RNG.integers(45, 720))
            orders_last_90d = int(RNG.integers(1, 8))
            is_priority_member = int(RNG.random() < 0.18)
            coupon_affinity = float(RNG.uniform(0.22, 0.55))
        elif segment_code == 2:
            tenure_days = int(RNG.integers(180, 1500))
            orders_last_90d = int(RNG.integers(4, 18))
            is_priority_member = int(RNG.random() < 0.48)
            coupon_affinity = float(RNG.uniform(0.10, 0.35))
        else:
            tenure_days = int(RNG.integers(365, 2600))
            orders_last_90d = int(RNG.integers(10, 42))
            is_priority_member = int(RNG.random() < 0.84)
            coupon_affinity = float(RNG.uniform(0.03, 0.18))

        customers.append(
            CustomerProfile(
                customer_id=f"C-{index + 1:07d}",
                city=city,
                latitude=latitude,
                longitude=longitude,
                segment_code=segment_code,
                tenure_days=tenure_days,
                orders_last_90d=orders_last_90d,
                is_priority_member=is_priority_member,
                coupon_affinity=coupon_affinity,
            )
        )

    return customers


def build_seller_pool(count: int) -> list[SellerProfile]:
    sellers: list[SellerProfile] = []

    for index in range(count):
        city, latitude, longitude = sample_location()
        seller_rating = round(float(RNG.uniform(3.6, 4.98)), 2)
        seller_orders_last_30d = int(max(20, round(RNG.lognormal(mean=5.9, sigma=0.75))))
        fulfilled_by_marketplace_bias = float(RNG.uniform(0.25, 0.92))
        express_bias = float(RNG.uniform(0.08, 0.72))

        sellers.append(
            SellerProfile(
                seller_id=f"S-{index + 1:06d}",
                city=city,
                latitude=latitude,
                longitude=longitude,
                seller_rating=seller_rating,
                seller_orders_last_30d=seller_orders_last_30d,
                fulfilled_by_marketplace_bias=fulfilled_by_marketplace_bias,
                express_bias=express_bias,
            )
        )

    return sellers


def category_unit_price(category_name: str) -> float:
    minimum, maximum = CATEGORY_PRICE_RANGES[category_name]
    return float(RNG.uniform(minimum, maximum))


def choose_fulfillment_mode(
    is_fulfilled_by_marketplace: int,
    is_priority_member: int,
    express_bias: float,
    warehouse_distance_km: float,
) -> int:
    same_day_weight = 0.0
    if is_fulfilled_by_marketplace and warehouse_distance_km <= 55:
        same_day_weight = 0.16 + (0.12 if is_priority_member else 0.0)

    express_weight = min(0.62, express_bias + (0.10 if is_priority_member else 0.0))
    standard_weight = max(0.08, 1.0 - express_weight - same_day_weight)
    weights = np.array([standard_weight, express_weight, same_day_weight], dtype=float)
    weights /= weights.sum()
    return int(RNG.choice([0, 1, 2], p=weights))


def promised_delivery_hours(
    fulfillment_mode_code: int,
    is_priority_member: int,
    warehouse_distance_km: float,
) -> int:
    if fulfillment_mode_code == 2:
        return int(RNG.integers(4, 18))
    if fulfillment_mode_code == 1:
        upper = 40 if is_priority_member else 52
        return int(RNG.integers(12, upper))

    base = int(RNG.integers(36, 120))
    if warehouse_distance_km > 240:
        base += int(RNG.integers(12, 36))
    return base


def actual_delivery(promised_hours: int, fulfillment_mode_code: int) -> int:
    if fulfillment_mode_code == 2:
        noise = int(round(RNG.normal(0, 4)))
    elif fulfillment_mode_code == 1:
        noise = int(round(RNG.normal(0, 7)))
    else:
        noise = int(round(RNG.normal(0, 14)))

    return max(1, promised_hours + noise)


def generate_row(
    index: int,
    customers: list[CustomerProfile],
    sellers: list[SellerProfile],
) -> dict[str, str | int | float]:
    customer = customers[int(RNG.integers(len(customers)))]
    seller = sellers[int(RNG.integers(len(sellers)))]

    channel_code = int(RNG.choice([0, 1], p=CHANNEL_WEIGHTS))
    payment_method_code = int(RNG.choice([0, 1, 2, 3], p=PAYMENT_WEIGHTS))

    base_items = customer.orders_last_90d / 8 + customer.segment_code * 1.3 + 1.6
    items_count = int(max(1, min(40, RNG.poisson(base_items) + 1)))
    unique_items_count = int(max(1, min(items_count, RNG.integers(max(1, items_count // 3), items_count + 1))))

    archetype_code = int(RNG.choice(np.arange(len(ORDER_ARCHETYPE_WEIGHTS)), p=ORDER_ARCHETYPE_WEIGHTS))
    category_counts = RNG.multinomial(items_count, ARCHETYPE_CATEGORY_WEIGHTS[archetype_code])
    (
        grocery_items_count,
        household_items_count,
        electronics_items_count,
        fashion_items_count,
        home_items_count,
    ) = [int(value) for value in category_counts]
    occupied_categories = sum(int(count > 0) for count in category_counts)
    unique_items_count = max(unique_items_count, occupied_categories)

    grocery_subtotal = grocery_items_count * category_unit_price("grocery")
    household_subtotal = household_items_count * category_unit_price("household")
    electronics_subtotal = electronics_items_count * category_unit_price("electronics")
    fashion_subtotal = fashion_items_count * category_unit_price("fashion")
    home_subtotal = home_items_count * category_unit_price("home")

    subtotal_amount = (
        grocery_subtotal
        + household_subtotal
        + electronics_subtotal
        + fashion_subtotal
        + home_subtotal
    )

    high_value_order = electronics_items_count > 0 or home_items_count >= 2 or subtotal_amount > 240
    is_fulfilled_by_marketplace = int(RNG.random() < seller.fulfilled_by_marketplace_bias)
    warehouse_distance_km = distance_km(
        customer.latitude,
        customer.longitude,
        seller.latitude,
        seller.longitude,
    )

    fulfillment_mode_code = choose_fulfillment_mode(
        is_fulfilled_by_marketplace=is_fulfilled_by_marketplace,
        is_priority_member=customer.is_priority_member,
        express_bias=seller.express_bias,
        warehouse_distance_km=warehouse_distance_km,
    )
    promised_hours = promised_delivery_hours(
        fulfillment_mode_code=fulfillment_mode_code,
        is_priority_member=customer.is_priority_member,
        warehouse_distance_km=warehouse_distance_km,
    )
    actual_delivery_hours = actual_delivery(promised_hours, fulfillment_mode_code)
    delay_hours = max(actual_delivery_hours - promised_hours, 0)

    coupon_used = int(RNG.random() < customer.coupon_affinity)
    coupon_discount_rate = float(RNG.uniform(0.04, 0.16)) if coupon_used else 0.0
    discount_cap = 45.0 if customer.segment_code >= 2 else 28.0
    discount_amount = min(subtotal_amount * coupon_discount_rate, discount_cap)

    shipping_base = [4.49, 7.49, 11.99][fulfillment_mode_code]
    shipping_distance_component = min(7.5, warehouse_distance_km * 0.012)
    shipping_bulk_component = max(0.0, items_count - 6) * 0.16
    shipping_fee = shipping_base + shipping_distance_component + shipping_bulk_component

    if customer.is_priority_member and is_fulfilled_by_marketplace:
        shipping_fee *= 0.15 if fulfillment_mode_code in {0, 1} else 0.45

    if subtotal_amount >= 85 and fulfillment_mode_code == 0:
        shipping_fee *= 0.55

    taxable_subtotal = max(0.0, subtotal_amount - discount_amount)
    weighted_tax_rate = (
        grocery_subtotal * CATEGORY_TAX_RATES["grocery"]
        + household_subtotal * CATEGORY_TAX_RATES["household"]
        + electronics_subtotal * CATEGORY_TAX_RATES["electronics"]
        + fashion_subtotal * CATEGORY_TAX_RATES["fashion"]
        + home_subtotal * CATEGORY_TAX_RATES["home"]
    ) / max(subtotal_amount, 1.0)
    subtotal_amount = round(subtotal_amount, 2)
    shipping_fee = round(shipping_fee, 2)
    discount_amount = round(discount_amount, 2)
    tax_amount = round(taxable_subtotal * weighted_tax_rate, 2)
    total_amount = round(subtotal_amount + shipping_fee + tax_amount - discount_amount, 2)
    avg_item_price = round(subtotal_amount / items_count, 2)

    marketplace_fee_rate = 0.09 + (0.03 if is_fulfilled_by_marketplace else 0.0) + (0.02 if high_value_order else 0.0)
    marketplace_fee_amount = round(subtotal_amount * marketplace_fee_rate, 2)

    return_probability = (
        0.018
        + 0.07 * (electronics_items_count > 0)
        + 0.09 * (fashion_items_count > 0)
        + 0.03 * (delay_hours >= 24)
        + 0.015 * (customer.segment_code == 0)
    )
    is_returned = int(RNG.random() < min(0.42, return_probability))
    returned_items_count = int(RNG.integers(1, items_count + 1)) if is_returned else 0
    refund_amount = 0.0
    if is_returned:
        refunded_share = returned_items_count / items_count
        refund_amount = min(total_amount, subtotal_amount * refunded_share + shipping_fee * 0.35)
    refund_amount = round(refund_amount, 2)

    fraud_signal = (
        0.12 * (customer.segment_code == 0)
        + 0.16 * (subtotal_amount > 350)
        + 0.10 * coupon_used
        + 0.08 * (payment_method_code == 3)
        + 0.08 * (warehouse_distance_km > 260)
    )
    cancellation_risk_score = min(1.0, fraud_signal + float(RNG.uniform(0.0, 0.28)))

    order_timestamp_epoch = int(RNG.integers(1704067200, 1735689600))
    order_hour = order_timestamp_epoch // 3600 % 24
    order_day_of_week = (order_timestamp_epoch // 86400 + 3) % 7

    return {
        "order_id": f"O-{index:08d}",
        "customer_id": customer.customer_id,
        "seller_id": seller.seller_id,
        "city": customer.city,
        "latitude": round(customer.latitude, 4),
        "longitude": round(customer.longitude, 4),
        "customer_segment_code": customer.segment_code,
        "seller_rating": seller.seller_rating,
        "seller_orders_last_30d": seller.seller_orders_last_30d,
        "is_fulfilled_by_marketplace": is_fulfilled_by_marketplace,
        "warehouse_distance_km": round(warehouse_distance_km, 2),
        "order_timestamp_epoch": order_timestamp_epoch,
        "order_hour": order_hour,
        "order_day_of_week": order_day_of_week,
        "channel_code": channel_code,
        "payment_method_code": payment_method_code,
        "items_count": items_count,
        "unique_items_count": unique_items_count,
        "grocery_items_count": grocery_items_count,
        "household_items_count": household_items_count,
        "electronics_items_count": electronics_items_count,
        "fashion_items_count": fashion_items_count,
        "home_items_count": home_items_count,
        "subtotal_amount": subtotal_amount,
        "shipping_fee": shipping_fee,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "avg_item_price": avg_item_price,
        "customer_tenure_days": customer.tenure_days,
        "customer_orders_last_90d": customer.orders_last_90d,
        "is_priority_member": customer.is_priority_member,
        "coupon_used": coupon_used,
        "fulfillment_mode_code": fulfillment_mode_code,
        "promised_delivery_hours": promised_hours,
        "actual_delivery_hours": actual_delivery_hours,
        "delay_hours": delay_hours,
        "is_returned": is_returned,
        "returned_items_count": returned_items_count,
        "refund_amount": refund_amount,
        "marketplace_fee_amount": marketplace_fee_amount,
        "cancellation_risk_score": round(cancellation_risk_score, 4),
    }


def write_dataset(output_path: str, row_count: int, flush_every: int) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    customer_pool = build_customer_pool(pool_size(row_count, minimum=5_000, maximum=100_000, divisor=10))
    seller_pool = build_seller_pool(pool_size(row_count, minimum=750, maximum=15_000, divisor=700))

    items_stats = RunningStats()
    total_amount_stats = RunningStats()
    delivery_delay_stats = RunningStats()

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = None

        for index in range(row_count):
            row = generate_row(index + 1, customer_pool, seller_pool)

            if writer is None:
                writer = csv.DictWriter(csv_file, fieldnames=list(row.keys()))
                writer.writeheader()

            writer.writerow(row)
            items_stats.update(float(row["items_count"]))
            total_amount_stats.update(float(row["total_amount"]))
            delivery_delay_stats.update(float(row["delay_hours"]))

            if flush_every > 0 and (index + 1) % flush_every == 0:
                csv_file.flush()

    print(f"Generated {row_count} rows -> {output_path}")
    print_stats("items_count", items_stats)
    print_stats("total_amount", total_amount_stats)
    print_stats("delay_hours", delivery_delay_stats)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic marketplace orders dataset")
    parser.add_argument("--size", type=int, default=1000, help="Number of rows to generate (default: 1000)")
    parser.add_argument("--output", default="data/orders.csv", help="Output CSV path")
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
