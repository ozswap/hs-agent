# Data Loader API Reference

The data loader module provides functionality for loading and searching HS code data.

::: hs_agent.core.data_loader.HSDataLoader
    options:
      docstring_style: numpy
      show_inheritance: true
      show_source: false

::: hs_agent.core.data_loader.HSCode
    options:
      docstring_style: numpy
      show_inheritance: true
      show_source: false

## Usage Examples

### Basic Data Loading

```python
from hs_agent.core.data_loader import HSDataLoader

# Initialize the data loader
loader = HSDataLoader("data")

# Load all HS code data
loader.load_all_data()

print(f"Loaded {len(loader.codes_2digit)} 2-digit codes")
print(f"Loaded {len(loader.codes_4digit)} 4-digit codes")
print(f"Loaded {len(loader.codes_6digit)} 6-digit codes")
```

### Searching HS Codes

```python
# Search for codes by description
candidates = loader.search_codes_by_description(
    "computer laptop",
    level=6,
    limit=5
)

for code, hs_code, score in candidates:
    print(f"{code}: {hs_code.description} (score: {score:.2f})")
```

### Hierarchical Navigation

```python
# Get child codes for a parent
children = loader.get_child_codes("84", target_level=4)
print(f"Found {len(children)} 4-digit codes under chapter 84")

# Get specific code details
code_info = loader.get_code_info("847130", level=6)
if code_info:
    print(f"Code: {code_info.code}")
    print(f"Description: {code_info.description}")
```

## Data Format

### CSV File Structure

The data loader expects CSV files with the following structure:

#### 2-digit codes (hs_codes_2digit.csv)
```csv
code,description
01,"Animals; live"
02,"Meat and edible meat offal"
```

#### 4-digit codes (hs_codes_4digit.csv)
```csv
code,description
0101,"Horses, asses, mules and hinnies; live"
0102,"Bovine animals; live"
```

#### 6-digit codes (hs_codes_6digit.csv)
```csv
code,description
010111,"Horses; live, pure-bred breeding animals"
010119,"Horses; live, other than pure-bred breeding animals"
```

#### Product Examples (product_examples.csv)
```csv
description,hs_code
"Pure-bred Arabian mare for breeding","010111"
"Fresh apples","080810"
```

## Performance Considerations

- **Loading Time**: Initial data loading may take several seconds for large datasets
- **Memory Usage**: All codes are loaded into memory for fast searching
- **Search Performance**: Text similarity search is optimized using TF-IDF vectorization
- **Caching**: Consider implementing caching for frequently accessed codes