"""Script to select 9 objects for validation study from subjective.csv and database.csv."""

import csv
import re
from collections import defaultdict

def extract_product_id(filename):
    """Extract product_id from 3D Object filename."""
    match = re.match(r'(\d+)', filename)
    return match.group(1) if match else None

# Load subjective scores
subjective_data = []
with open('subjective.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        product_id = extract_product_id(row['3D Object filename'])
        if product_id:
            row['product_id'] = product_id
            subjective_data.append(row)

# Load database
database_data = {}
with open('database.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row['product_id']
        if pid not in database_data:  # Keep first occurrence
            database_data[pid] = row

# Merge data
merged_data = []
for subj_row in subjective_data:
    pid = subj_row['product_id']
    if pid in database_data:
        db_row = database_data[pid]
        merged_row = {
            'product_id': pid,
            '3D Object filename': subj_row['3D Object filename'],
            'Visual Fidelity': float(subj_row['Visual Fidelity']),
            'product_name': db_row['product_name'],
            'manufacturer': db_row['manufacturer'],
            'category_l1': db_row['category_l1'],
            'category_l2': db_row['category_l2'],
            'category_l3': db_row['category_l3'],
            'output_glb_relpath': db_row['output_glb_relpath'],
            'variant': db_row.get('variant', '')
        }
        merged_data.append(merged_row)

# Group by l3 category
category_groups = defaultdict(list)
for row in merged_data:
    cat = row['category_l3']
    if cat and cat.strip():
        category_groups[cat].append(row)

# Print available categories
print("=" * 80)
print("AVAILABLE L3 CATEGORIES WITH COUNTS:")
print("=" * 80)
for cat in sorted(category_groups.keys(), key=lambda x: len(category_groups[x]), reverse=True):
    items = category_groups[cat]
    manufacturers = set([item['manufacturer'] for item in items if item['manufacturer']])
    print(f"{cat:40s}: {len(items):3d} items, {len(manufacturers):2d} manufacturers")

# Select top 3 categories
top_categories = sorted(category_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]

print("\n" + "=" * 80)
print("TOP 5 CATEGORIES FOR SELECTION:")
print("=" * 80)

selected_objects = []
selected_categories = []

for cat_name, items in top_categories:
    print(f"\n{cat_name} ({len(items)} items):")
    print("-" * 80)

    # Group by manufacturer
    mfg_groups = defaultdict(list)
    for item in items:
        mfg_groups[item['manufacturer']].append(item)

    print(f"  Manufacturers: {', '.join(mfg_groups.keys())}")

    # Select 3 objects from different manufacturers if possible
    selected_for_category = []
    used_manufacturers = set()

    # Sort manufacturers by number of items (to get diverse selection)
    for mfg in sorted(mfg_groups.keys()):
        if len(selected_for_category) < 3 and mfg not in used_manufacturers:
            # Select one object from this manufacturer with high VF score
            mfg_items = sorted(mfg_groups[mfg], key=lambda x: x['Visual Fidelity'], reverse=True)
            if mfg_items:
                selected_for_category.append(mfg_items[0])
                used_manufacturers.add(mfg)

    # If we don't have 3 yet, add more from any manufacturer
    if len(selected_for_category) < 3:
        all_items = sorted(items, key=lambda x: x['Visual Fidelity'], reverse=True)
        for item in all_items:
            if item not in selected_for_category and len(selected_for_category) < 3:
                selected_for_category.append(item)

    # Print selected objects
    for obj in selected_for_category:
        print(f"    - {obj['product_id']:6s} | {obj['manufacturer']:20s} | "
              f"{obj['product_name']:25s} | VF: {obj['Visual Fidelity']:.3f}")

    if len(selected_for_category) == 3:
        selected_categories.append(cat_name)
        selected_objects.extend(selected_for_category)

    if len(selected_categories) == 3:
        break

print("\n" + "=" * 80)
print("FINAL SELECTION (9 OBJECTS FROM 3 CATEGORIES):")
print("=" * 80)

for i, obj in enumerate(selected_objects, 1):
    print(f"{i}. Product ID: {obj['product_id']}")
    print(f"   Category: {obj['category_l3']}")
    print(f"   Name: {obj['product_name']}")
    print(f"   Manufacturer: {obj['manufacturer']}")
    print(f"   Visual Fidelity: {obj['Visual Fidelity']:.3f}")
    print(f"   3D File: {obj['3D Object filename']}")
    print()

# Save selection
with open('selected_objects_for_study.csv', 'w', newline='', encoding='utf-8') as f:
    if selected_objects:
        fieldnames = selected_objects[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_objects)

print(f"Selection saved to 'selected_objects_for_study.csv'")
