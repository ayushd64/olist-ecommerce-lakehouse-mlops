
from pathlib import Path
import pandas as pd


# ==================================================
# 1. CONFIGURATION
# ==================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
DOCS_DIR = ROOT / "docs"

DOCS_DIR.mkdir(parents=True, exist_ok=True)


def read_columns(filename, columns):

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(path)

    # Preserve IDs and postal-code prefixes as strings.
    dtype = {
        column: "string"
        for column in columns
    }

    return pd.read_csv(
        path,
        usecols=columns,
        dtype=dtype,
        low_memory=False
    )


# ==================================================
# 2. CANDIDATE PRIMARY KEY VALIDATION
# ==================================================

def validate_candidate_keys():

    print("\n========== PRIMARY KEY VALIDATION ==========")

    definitions = {
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
            "keys": ["review_id", "order_id"]
        },
        "products": {
            "file": "olist_products_dataset.csv",
            "keys": ["product_id"]
        },
        "sellers": {
            "file": "olist_sellers_dataset.csv",
            "keys": ["seller_id"]
        },
        "category_translation": {
            "file": "product_category_name_translation.csv",
            "keys": ["product_category_name"]
        }
    }

    results = []

    for table, definition in definitions.items():

        keys = definition["keys"]

        df = read_columns(
            definition["file"],
            keys
        )

        null_mask = df[keys].isna().any(axis=1)

        complete_keys = df.loc[~null_mask, keys]

        duplicate_mask = complete_keys.duplicated(
            subset=keys,
            keep=False
        )

        duplicate_rows = int(duplicate_mask.sum())

        duplicate_groups = int(
            complete_keys.loc[duplicate_mask]
            .drop_duplicates()
            .shape[0]
        )

        result = {
            "table": table,
            "candidate_key": " + ".join(keys),
            "total_rows": len(df),
            "null_key_rows": int(null_mask.sum()),
            "duplicate_key_groups": duplicate_groups,
            "duplicate_key_rows": duplicate_rows,
            "is_unique": (
                null_mask.sum() == 0
                and duplicate_rows == 0
            )
        }

        results.append(result)

        print(f"\nTable: {table}")
        print("Candidate key:", keys)
        print("Null key rows:", result["null_key_rows"])
        print("Duplicate groups:", duplicate_groups)
        print("Duplicate rows:", duplicate_rows)
        print("Unique:", result["is_unique"])

    output = pd.DataFrame(results)

    output.to_csv(
        DOCS_DIR / "key_validation.csv",
        index=False
    )

    return output


# ==================================================
# 3. FOREIGN KEY VALIDATION
# ==================================================

def validate_foreign_key(
    relationship,
    child_file,
    child_column,
    parent_file,
    parent_column
):

    child = read_columns(
        child_file,
        [child_column]
    )

    parent = read_columns(
        parent_file,
        [parent_column]
    )

    parent_values = set(
        parent[parent_column].dropna().tolist()
    )

    child_values = child[child_column]

    null_mask = child_values.isna()

    orphan_mask = (
        child_values.notna()
        & ~child_values.isin(parent_values)
    )

    orphan_values = (
        child_values[orphan_mask]
        .drop_duplicates()
        .tolist()
    )

    result = {
        "relationship": relationship,
        "child_file": child_file,
        "child_column": child_column,
        "parent_file": parent_file,
        "parent_column": parent_column,
        "child_rows": len(child),
        "null_foreign_key_rows": int(null_mask.sum()),
        "orphan_rows": int(orphan_mask.sum()),
        "distinct_orphan_keys": len(orphan_values),
        "orphan_sample": ", ".join(
            str(value) for value in orphan_values[:5]
        )
    }

    print(f"\nRelationship: {relationship}")
    print("Child rows:", result["child_rows"])
    print("Null FK rows:", result["null_foreign_key_rows"])
    print("Orphan rows:", result["orphan_rows"])
    print("Distinct orphan keys:", result["distinct_orphan_keys"])
    print("Sample orphan keys:", result["orphan_sample"] or "None")

    return result


def validate_foreign_keys():

    print("\n========== FOREIGN KEY VALIDATION ==========")

    relationships = [
        (
            "orders.customer_id -> customers.customer_id",
            "olist_orders_dataset.csv",
            "customer_id",
            "olist_customers_dataset.csv",
            "customer_id"
        ),
        (
            "items.order_id -> orders.order_id",
            "olist_order_items_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id"
        ),
        (
            "items.product_id -> products.product_id",
            "olist_order_items_dataset.csv",
            "product_id",
            "olist_products_dataset.csv",
            "product_id"
        ),
        (
            "items.seller_id -> sellers.seller_id",
            "olist_order_items_dataset.csv",
            "seller_id",
            "olist_sellers_dataset.csv",
            "seller_id"
        ),
        (
            "payments.order_id -> orders.order_id",
            "olist_order_payments_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id"
        ),
        (
            "reviews.order_id -> orders.order_id",
            "olist_order_reviews_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id"
        ),
        (
            "customers.zip -> geolocation.zip",
            "olist_customers_dataset.csv",
            "customer_zip_code_prefix",
            "olist_geolocation_dataset.csv",
            "geolocation_zip_code_prefix"
        ),
        (
            "sellers.zip -> geolocation.zip",
            "olist_sellers_dataset.csv",
            "seller_zip_code_prefix",
            "olist_geolocation_dataset.csv",
            "geolocation_zip_code_prefix"
        ),
        (
            "products.category -> translation.category",
            "olist_products_dataset.csv",
            "product_category_name",
            "product_category_name_translation.csv",
            "product_category_name"
        )
    ]

    results = []

    for relationship in relationships:

        results.append(
            validate_foreign_key(*relationship)
        )

    output = pd.DataFrame(results)

    output.to_csv(
        DOCS_DIR / "foreign_key_validation.csv",
        index=False
    )

    return output


# ==================================================
# 4. MAIN
# ==================================================

def main():

    print("=" * 60)
    print("OLIST RELATIONSHIP VALIDATION")
    print("=" * 60)

    if not DATA_DIR.exists():
        raise FileNotFoundError(DATA_DIR)

    primary_key_results = validate_candidate_keys()

    foreign_key_results = validate_foreign_keys()

    print("\n========== SUMMARY ==========")

    print("\nCandidate keys:")
    print(
        primary_key_results[
            ["table", "is_unique"]
        ].to_string(index=False)
    )

    print("\nForeign keys:")
    print(
        foreign_key_results[
            [
                "relationship",
                "null_foreign_key_rows",
                "orphan_rows"
            ]
        ].to_string(index=False)
    )

    print("\nReports generated:")
    print("docs/key_validation.csv")
    print("docs/foreign_key_validation.csv")

    print("\nRELATIONSHIP VALIDATION COMPLETED")


if __name__ == "__main__":
    main()
