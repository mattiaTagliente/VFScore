"""Select 9 objects MAXIMIZING manufacturer and category diversity."""

import csv
from collections import defaultdict

# Load subjective scores
subjective_data = []
with open('subjective.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        import re
        match = re.match(r'(\d+)', row['3D Object filename'])
        if match:
            row['product_id'] = match.group(1)
            row['Visual Fidelity'] = float(row['Visual Fidelity'])
            subjective_data.append(row)

# Load database
database_data = {}
with open('database.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row['product_id']
        if pid not in database_data:
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
            'Visual Fidelity': subj_row['Visual Fidelity'],
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

# Group by manufacturer
manufacturer_groups = defaultdict(list)
for row in merged_data:
    mfg = row['manufacturer']
    if mfg and mfg.strip():
        manufacturer_groups[mfg].append(row)

print("=" * 80)
print("MANUFACTURER DIVERSITY ANALYSIS")
print("=" * 80)
for mfg in sorted(manufacturer_groups.keys(), key=lambda x: len(manufacturer_groups[x]), reverse=True):
    items = manufacturer_groups[mfg]
    categories = set([item['category_l3'] for item in items if item['category_l3']])
    print(f"{mfg:30s}: {len(items):3d} items across {len(categories):2d} L3 categories")

print("\n" + "=" * 80)
print("CATEGORY × MANUFACTURER MATRIX")
print("=" * 80)

# Build category-manufacturer matrix
cat_mfg_matrix = defaultdict(lambda: defaultdict(list))
for row in merged_data:
    cat = row['category_l3']
    mfg = row['manufacturer']
    if cat and mfg:
        cat_mfg_matrix[cat][mfg].append(row)

# Find categories with maximum manufacturer diversity
diverse_categories = []
for cat in sorted(cat_mfg_matrix.keys()):
    mfgs = list(cat_mfg_matrix[cat].keys())
    if len(mfgs) >= 1:  # At least some manufacturers
        diverse_categories.append((cat, len(mfgs), mfgs))

# Sort by number of manufacturers (descending), then by total items
diverse_categories.sort(key=lambda x: (x[1], sum(len(cat_mfg_matrix[x[0]][m]) for m in x[2])), reverse=True)

print(f"\n{'Category':<40s} {'#Mfgs':<6s} {'Manufacturers'}")
print("-" * 80)
for cat, n_mfgs, mfgs in diverse_categories[:10]:
    print(f"{cat:<40s} {n_mfgs:<6d} {', '.join(mfgs[:5])}")

# STRATEGY: Select 3 categories with MAXIMUM manufacturer diversity
# For each category, select 3 objects from DIFFERENT manufacturers if possible

print("\n" + "=" * 80)
print("OPTIMAL SELECTION STRATEGY")
print("=" * 80)

selected_objects = []
selected_categories = []

# Select top 3 most diverse categories
target_categories = diverse_categories[:3]

for cat, n_mfgs, mfgs in target_categories:
    print(f"\n{cat} ({n_mfgs} manufacturers: {', '.join(mfgs)})")
    print("-" * 80)

    selected_for_category = []

    # Try to get one object from each manufacturer in this category
    for mfg in mfgs:
        if len(selected_for_category) >= 3:
            break

        items = cat_mfg_matrix[cat][mfg]
        # Select best scoring item from this manufacturer
        best_item = max(items, key=lambda x: x['Visual Fidelity'])
        selected_for_category.append(best_item)
        print(f"  [{mfg}] {best_item['product_id']:6s} - {best_item['product_name']:30s} VF={best_item['Visual Fidelity']:.3f}")

    # If we still need more objects (category has fewer than 3 manufacturers)
    if len(selected_for_category) < 3:
        # Get all items from this category not yet selected
        all_cat_items = []
        for mfg in mfgs:
            all_cat_items.extend(cat_mfg_matrix[cat][mfg])

        # Remove already selected
        remaining = [item for item in all_cat_items if item not in selected_for_category]
        # Sort by VF score and take top ones
        remaining.sort(key=lambda x: x['Visual Fidelity'], reverse=True)

        needed = 3 - len(selected_for_category)
        for item in remaining[:needed]:
            selected_for_category.append(item)
            print(f"  [{item['manufacturer']}] {item['product_id']:6s} - {item['product_name']:30s} VF={item['Visual Fidelity']:.3f} (supplemental)")

    selected_categories.append(cat)
    selected_objects.extend(selected_for_category[:3])  # Ensure exactly 3

print("\n" + "=" * 80)
print("FINAL OPTIMIZED SELECTION (9 OBJECTS)")
print("=" * 80)

# Analyze final selection diversity
final_manufacturers = set([obj['manufacturer'] for obj in selected_objects])
final_categories = set([obj['category_l3'] for obj in selected_objects])

print(f"\nDiversity Metrics:")
print(f"  Unique Manufacturers: {len(final_manufacturers)}")
print(f"  Unique L3 Categories: {len(final_categories)}")
print(f"  Total Objects: {len(selected_objects)}")

print(f"\nManufacturers: {', '.join(sorted(final_manufacturers))}")
print(f"\nCategories: {', '.join(sorted(final_categories))}")

print("\n" + "-" * 80)
for i, obj in enumerate(selected_objects, 1):
    print(f"{i}. [{obj['category_l3']}]")
    print(f"   Product: {obj['product_id']} - {obj['product_name']}")
    print(f"   Manufacturer: {obj['manufacturer']}")
    print(f"   Visual Fidelity: {obj['Visual Fidelity']:.3f}")
    print(f"   File: {obj['3D Object filename']}")
    print()

# Save selection
with open('selected_objects_optimized.csv', 'w', newline='', encoding='utf-8') as f:
    if selected_objects:
        fieldnames = selected_objects[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_objects)

print(f"Selection saved to 'selected_objects_optimized.csv'")
