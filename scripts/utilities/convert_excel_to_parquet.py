import pandas as pd
import os

def convert_excel_to_parquet(excel_path, parquet_path):
    """Convert Excel file to Parquet format and return file size info."""

    # Read Excel file
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)

    # Display basic info about the data
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    print(f"Data types:\n{df.dtypes}")

    # Convert gmail_id to string to handle mixed types
    if 'gmail_id' in df.columns:
        df['gmail_id'] = df['gmail_id'].astype(str)

    # Convert date_received to datetime if it's not already
    if 'date_received' in df.columns:
        df['date_received'] = pd.to_datetime(df['date_received'], format='mixed', errors='coerce')

    # Convert to Parquet
    print(f"Converting to Parquet: {parquet_path}")
    df.to_parquet(parquet_path, compression='snappy')

    # Get file sizes
    excel_size = os.path.getsize(excel_path)
    parquet_size = os.path.getsize(parquet_path)

    print(f"\nFile size comparison:")
    print(f"Excel file: {excel_size:,} bytes ({excel_size / 1024 / 1024:.2f} MB)")
    print(f"Parquet file: {parquet_size:,} bytes ({parquet_size / 1024 / 1024:.2f} MB)")
    print(f"Compression ratio: {excel_size / parquet_size:.2f}x smaller")

    return parquet_size

if __name__ == "__main__":
    excel_file = r"C:\Users\lucia\Downloads\data.xlsx"
    parquet_file = r"C:\Users\lucia\Downloads\data.parquet"

    try:
        file_size = convert_excel_to_parquet(excel_file, parquet_file)
        print(f"\nParquet file character count: {file_size:,} bytes")

    except FileNotFoundError:
        print(f"Error: Excel file not found at {excel_file}")
    except Exception as e:
        print(f"Error: {e}")