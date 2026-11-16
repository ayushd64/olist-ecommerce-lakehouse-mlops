from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "raw"
DOCS_DIR = PROJECT_ROOT / "docs"

DOCS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Expected source files
# --------------------------------------------------

DATASETS = {
    "customers": {
        "file": "olist_customers_dataset.csv",
        "keys": ["customer_id"]
    },
    "orders": {
        "file": "olist_orders_dataset.csv",
        "keys": ["order_id"]
    },
    "order_items": {
        "file": "olist_order_items_dataset.csv",
        "keys": ["order_id", "order_item_id"]
    },
    "payments": {
        "file": "olist_order_payments_dataset.csv",
        "keys": ["order_id", "payment_sequential"]
    },
    "reviews": {
        "file": "olist_order_reviews_dataset.csv",
        "keys": ["review_id"]
    },
    "products": {
        "file": "olist_products_dataset.csv",
        "keys": ["product_id"]
    },
    "sellers": {
        "file": "olist_sellers_dataset.csv",
        "keys": ["seller_id"]
    },
    "geolocation": {
        "file": "olist_geolocation_dataset.csv",
        "keys": []
    },
    "category_translation": {
        "file": "product_category_name_translation.csv",
        "keys": ["product_category_name"]
    }
}


# --------------------------------------------------
# 3. Check expected files
# --------------------------------------------------

missing_files = [
    details["file"]
    for details in DATASETS.values()
    if not (DATA_DIR / details["file"]).exists()
]

if missing_files:
    raise FileNotFoundError(
        f"Missing dataset files: {missing_files}\n"
        f"Expected directory: {DATA_DIR}"
    )


# --------------------------------------------------
# 4. Profile each dataset
# --------------------------------------------------

inventory = []
schema_profile = []
quality_profile = []

for name, details in DATASETS.items():

    file_path = DATA_DIR / details["file"]

    print(f"\n{'=' * 60}")
    print(f"Profiling: {name}")
    print(f"{'=' * 60}")

    # Read one CSV at a time to limit memory usage.
    df = pd.read_csv(file_path, low_memory=False)

    row_count, column_count = df.shape

    memory_mb = (
        df.memory_usage(deep=True).sum() / (1024 ** 2)
    )

    key_columns = details["keys"]

    # Check candidate primary key uniqueness.
    if key_columns:
        available_keys = [
            col for col in key_columns if col in df.columns
        ]

        if len(available_keys) == len(key_columns):
            duplicate_key_rows = int(
                df.duplicated(
                    subset=key_columns,
                    keep=False
                ).sum()
            )
            null_key_rows = int(
                df[key_columns].isna().any(axis=1).sum()
            )
        else:
            duplicate_key_rows = None
            null_key_rows = None
    else:
        duplicate_key_rows = None
        null_key_rows = None

    # Full-row duplicate detection.
    duplicate_rows = int(df.duplicated().sum())

    total_missing = int(df.isna().sum().sum())

    # Dataset inventory.
    inventory.append({
        "dataset": name,
        "file_name": details["file"],
        "row_count": row_count,
        "column_count": column_count,
        "memory_mb": round(memory_mb, 2),
        "columns": ", ".join(df.columns)
    })

    # Column-level schema profile.
    for column in df.columns:

        missing_count = int(df[column].isna().sum())

        schema_profile.append({
            "dataset": name,
            "column_name": column,
            "data_type": str(df[column].dtype),
            "missing_count": missing_count,
            "missing_percentage": round(
                (missing_count / row_count) * 100, 2
            ) if row_count else 0
        })

    # Dataset-level quality profile.
    quality_profile.append({
        "dataset": name,
        "total_rows": row_count,
        "duplicate_full_rows": duplicate_rows,
        "duplicate_candidate_key_rows": duplicate_key_rows,
        "null_candidate_key_rows": null_key_rows,
        "total_missing_values": total_missing
    })

    print("Shape:", df.shape)
    print("Memory (MB):", round(memory_mb, 2))
    print("Duplicate rows:", duplicate_rows)
    print("Missing values:", total_missing)

    if key_columns:
        print("Candidate key:", key_columns)
        print("Duplicate key rows:", duplicate_key_rows)

    del df


# --------------------------------------------------
# 5. Save profiling reports
# --------------------------------------------------

pd.DataFrame(inventory).to_csv(
    DOCS_DIR / "data_inventory.csv",
    index=False
)

pd.DataFrame(schema_profile).to_csv(
    DOCS_DIR / "schema_profile.csv",
    index=False
)

pd.DataFrame(quality_profile).to_csv(
    DOCS_DIR / "quality_profile.csv",
    index=False
)


print("\n" + "=" * 60)
print("DATA PROFILING COMPLETED")
print("=" * 60)

print("Generated files:")
print("1. docs/data_inventory.csv")
print("2. docs/schema_profile.csv")
print("3. docs/quality_profile.csv")