"""
Beta code converter using TLGU implementation.

Converts TLG/PHI beta code files to Unicode with standardized citation formatting.
"""

import argparse
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def convert_file(input_path: str, output_path: str) -> bool:
    """Convert a single beta code file to Unicode."""
    try:
        logger.info(f"Converting {input_path} to {output_path}")
        
        # Combine working format with our recommended citation format
        cmd = f"tlgu -b -W -Z'%w/%x/%y/%z\t' '-e - ' {input_path} {output_path}"
        logger.info(f"Running command: {cmd}")
        
        # Run command through shell
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully converted to {output_path}")
            return True
        else:
            logger.error(f"Conversion failed: {result.stderr}")
            return False
                
    except Exception as e:
        logger.error(f"Error converting file {input_path}: {str(e)}")
        return False

def convert_directory(input_dir: str, output_dir: str) -> None:
    """Convert all TLG files in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for input_file in input_dir.glob("*.TXT"):
        output_file = output_dir / f"{input_file.stem}_unicode.txt"
        convert_file(str(input_file), str(output_file))

def main():
    parser = argparse.ArgumentParser(description="Convert TLG beta code files to Unicode")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("output", help="Output file or directory")
    parser.add_argument("-d", "--directory", action="store_true", help="Process directory")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.directory:
        convert_directory(args.input, args.output)
    else:
        convert_file(args.input, args.output)

if __name__ == "__main__":
    main()

#example: python toolkit/migration/beta_converter.py assets/beta_files/TLG0627.TXT texts/TLG0627_hippocrates
