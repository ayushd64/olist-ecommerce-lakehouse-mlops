
# Olist Dataset — Data Quality Findings

## 1. Dataset Overview

- Source: Olist Brazilian E-Commerce Public Dataset
- Number of source files: 9
- Total source records: 1,550,922
- Total source columns: 52

## 2. Primary Key Validation

All eight candidate primary keys passed validation.

| Table | Candidate key | Result |
|---|---|---|
| Customers | customer_id | Passed |
| Orders | order_id | Passed |
| Order Items | order_id + order_item_id | Passed |
| Payments | order_id + payment_sequential | Passed |
| Reviews | review_id + order_id | Passed |
| Products | product_id | Passed |
| Sellers | seller_id | Passed |
| Category Translation | product_category_name | Passed |

Note: review_id alone is not unique.

## 3. Foreign Key Validation

### Core transactional relationships

All six core relationships have zero null foreign keys
and zero orphan records.

- Orders -> Customers
- Order Items -> Orders
- Order Items -> Products
- Order Items -> Sellers
- Payments -> Orders
- Reviews -> Orders

### Lookup relationships

Customers to Geolocation:
- 278 unmatched customer records.
- 157 distinct unmatched ZIP prefixes.

Sellers to Geolocation:
- 7 unmatched seller records.
- 7 distinct unmatched ZIP prefixes.

Products to Category Translation:
- 610 products with missing category values.
- 13 product rows with untranslated category values.
- 2 distinct unmatched category values.

Unmatched lookup values will not cause source records to
be deleted.

## 4. Data Quality Findings

### Orders
- 4,908 missing timestamp values.
- 8 delivered orders lack actual delivery timestamps.
- Missing timestamps will be analyzed according to order status.

### Reviews
- 1,603 rows involved in repeated review IDs.
- 789 repeated review ID groups.
- review_id + order_id is unique.
- Review comments are optional fields.

### Products
- 610 products have missing category information.
- 610 products have missing name and description lengths.
- Two products lack all four physical measurement attributes.

### Geolocation
- 1,000,163 raw rows.
- 261,831 exact duplicate rows.
- 738,332 rows after exact deduplication.
- 19,015 distinct ZIP prefixes.
- Multiple coordinates can belong to the same ZIP prefix.

## 5. Machine Learning Target

Target: is_late

Definition:
1 when actual delivery is later than estimated delivery.
0 when actual delivery is on or before estimated delivery.

Initial eligible dataset:
- 96,470 delivered orders.

Class distribution:
- On-time: 88,644 (91.89%)
- Late: 7,826 (8.11%)

Due to class imbalance, model evaluation will prioritize
Recall, Precision, F1-score and PR-AUC rather than accuracy
alone.

## 6. Data Engineering Decisions

- Bronze preserves original source records.
- Silver performs cleaning and validation.
- Geolocation is deduplicated and aggregated by ZIP prefix.
- Geolocation enrichment uses LEFT JOIN.
- Category translation uses LEFT JOIN.
- Reviews use review_id + order_id as a candidate key.
- Missing values are handled according to business meaning.
- No invalid records are deleted without investigation.

## 7. Conclusion

Core transactional relationships passed validation.
Lookup coverage gaps and optional missing values have been
documented for downstream processing.
