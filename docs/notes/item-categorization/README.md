# Item Categorization

## Idea

Use practical household categories for day-to-day use, with optional mapping to public classification standards when useful.

## Practical Household Categories

```text
Clothing & Accessories
Tools & Hardware
Cables & Electronics
Kitchen & Dining
Documents & Paper
Seasonal & Holiday
Sports & Camping
Toys & Games
Books & Media
Home Decor
Cleaning & Household Supplies
Crafts & Hobbies
Sentimental / Keepsakes
Donate / Sell
Unknown / Needs Review
```

## Public Standards To Consider

### UNSPSC

Useful global product/service classification. Likely the best optional mapping if the app needs standard codes.

### GS1 GPC

Retail/product-data oriented. Useful for consumer goods and barcode/product-style categorization.

### Federal Supply Classification / NATO Supply Classification

Military/government logistics classification. Openly available and real, but probably too procurement-oriented for the main user-facing taxonomy.

## Recommendation

Use household categories in the interface. Store optional standard mapping fields in the background:

```text
category_name
standard_system
standard_code
standard_label
```

## Photo Workflow Note

Do not require individual photos for every item. Better workflow:

```text
Photo 1: everything laid out, top-down
Photo 2: small or overlapping items closer up
Photo 3: labels, serial numbers, model stickers, or documents
```

