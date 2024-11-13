# Beta Code Converter

This tool converts TLG/PHI beta code files to Unicode with standardized citation formatting using CLTK's TLGU implementation.

## Features

- Converts beta code to Unicode text
- Standardizes citation format using x/y/z hierarchy levels
- Handles both single files and directories
- Preserves citation information with proper formatting
- Uses tab character to separate citations from text

## Installation

Requires CLTK package:
```bash
pip install cltk
```

## Usage

### Command Line Interface

1. Convert a single file:
```bash
python beta_converter.py input.txt -o output.txt
```

2. Convert all files in a directory:
```bash
python beta_converter.py input_dir/ -o output_dir/
```

### Python API

```python
from beta_converter import BetaConverter

# Initialize converter
converter = BetaConverter()

# Convert single file
converter.convert_file("input.txt", "output.txt")

# Convert directory
converted_files = converter.convert_directory("input_dir/", "output_dir/")
```

## Citation Format

The converter uses TLGU's citation formatting options:
- Format: `x/y/z\t` where:
  * x: highest level (e.g., book)
  * y: middle level (e.g., chapter)
  * z: lowest level (e.g., line)
  * \t: tab separator between citation and text
- Empty citation levels are filled with "-"

Example output:
```
1/2/3\tText content here...
1/2/4\tMore text content...
1/3/-\tSection with no line number...
```

## Error Handling

- Logs errors and warnings
- Returns boolean success status for single file conversion
- Returns list of successfully converted files for directory conversion
- Creates output directories if they don't exist

## Dependencies

- Python 3.6+
- CLTK library
- pathlib (standard library)
- argparse (standard library)
- logging (standard library)
