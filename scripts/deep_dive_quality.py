from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"


def load_dataset(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    return pd.read_csv(path, low_memory=False)


# --------------------------------------------------
# 2. Orders: missing timestamps by order status
# --------------------------------------------------

print("\n========== ORDERS ANALYSIS ==========")

orders = load_dataset("olist_orders_dataset.csv")

timestamp_columns = [
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

print("\nMissing values by column:")
print(orders[timestamp_columns].isna().sum())

print("\nMissing timestamps by order status:")

status_report = (
    orders.groupby("order_status")
    .agg(
        total_orders=("order_id", "count"),
        missing_approval=("order_approved_at", lambda x: x.isna().sum()),
        missing_carrier=("order_delivered_carrier_date", lambda x: x.isna().sum()),
        missing_delivery=("order_delivered_customer_date", lambda x: x.isna().sum()),
        missing_estimate=("order_estimated_delivery_date", lambda x: x.isna().sum())
    )
)

print(status_report)


# Check initial eligible ML population

eligible_orders = orders[
    (orders["order_status"] == "delivered")
    & orders["order_delivered_customer_date"].notna()
    & orders["order_estimated_delivery_date"].notna()
].copy()

eligible_orders["order_delivered_customer_date"] = pd.to_datetime(
    eligible_orders["order_delivered_customer_date"],
    errors="coerce"
)

eligible_orders["order_estimated_delivery_date"] = pd.to_datetime(
    eligible_orders["order_estimated_delivery_date"],
    errors="coerce"
)

eligible_orders["is_late"] = (
    eligible_orders["order_delivered_customer_date"]
    > eligible_orders["order_estimated_delivery_date"]
).astype("int8")

print("\nEligible delivery prediction records:", len(eligible_orders))

print("\nTarget distribution:")
print(eligible_orders["is_late"].value_counts())

print("\nTarget percentage:")
print(eligible_orders["is_late"].value_counts(normalize=True) * 100)


# --------------------------------------------------
# 3. Reviews: candidate key investigation
# --------------------------------------------------

print("\n========== REVIEWS ANALYSIS ==========")

reviews = load_dataset("olist_order_reviews_dataset.csv")

print("\nMissing values by column:")
print(reviews.isna().sum())

# Count duplicated review IDs
review_counts = reviews.groupby("review_id", dropna=False).size()

duplicate_review_ids = review_counts[review_counts > 1]

print("\nNumber of repeated review IDs:",
      len(duplicate_review_ids))

print("\nRows involved in repeated review IDs:",
      int(reviews.duplicated("review_id", keep=False).sum()))

print("\nAdditional occurrences beyond first occurrence:",
      int(reviews.duplicated("review_id", keep="first").sum()))

# Check whether repeated review IDs belong to multiple orders

duplicate_review_records = reviews[
    reviews["review_id"].isin(duplicate_review_ids.index)
]

multi_order_review_ids = (
    duplicate_review_records.groupby("review_id")["order_id"]
    .nunique()
)

print("\nRepeated review IDs associated with multiple orders:",
      int((multi_order_review_ids > 1).sum()))

# Test composite key
print("\nDuplicate rows using review_id + order_id:",
      int(reviews.duplicated(
          ["review_id", "order_id"],
          keep=False
      ).sum()))

print("\nReview records per order:")
print(reviews.groupby("order_id").size().describe())


# --------------------------------------------------
# 4. Products: missing-value investigation
# --------------------------------------------------

print("\n========== PRODUCTS ANALYSIS ==========")

products = load_dataset("olist_products_dataset.csv")

print("\nMissing values by column:")
print(products.isna().sum())

print("\nProducts missing category:",
      products["product_category_name"].isna().sum())

print("\nProducts missing all four physical attributes:")

physical_columns = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

all_physical_missing = products[physical_columns].isna().all(axis=1)

print(int(all_physical_missing.sum()))


# --------------------------------------------------
# 5. Geolocation: duplicate investigation
# --------------------------------------------------

print("\n========== GEOLOCATION ANALYSIS ==========")

geo = load_dataset("olist_geolocation_dataset.csv")

exact_duplicates = int(geo.duplicated().sum())

print("\nTotal geolocation rows:", len(geo))

print("Exact duplicate rows:", exact_duplicates)

print("Rows after exact deduplication:",
      len(geo.drop_duplicates()))

zip_column = "geolocation_zip_code_prefix"

print("\nDistinct ZIP prefixes:", geo[zip_column].nunique())

zip_counts = geo.groupby(zip_column).size()

print("\nCoordinates per ZIP prefix:")
print(zip_counts.describe())

print("\nMaximum coordinate records for one ZIP prefix:",
      int(zip_counts.max()))


# --------------------------------------------------
# 6. End
# --------------------------------------------------

print("\n========== DEEP DIVE COMPLETED ==========")