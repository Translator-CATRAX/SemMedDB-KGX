"""Download and extract the uncapped SemMedDB data from S3.

Usage:
    python download_semmeddb_uncapped.py

Downloads the tar.gz archive from S3 and extracts all files into data/.
Nested directory structure is flattened so all files are directly accessible.
"""

import tarfile
import urllib.request
from pathlib import Path

S3_URL = "https://rtx-kg2-public.s3.us-west-2.amazonaws.com/kg2.10.3_semmeddb_dogpark_uncapped_2026_04_07.tar.gz"

OUTPUT_DIR = Path("data")
ARCHIVE_FILENAME = "kg2.10.3_semmeddb_dogpark_uncapped_2026_04_07.tar.gz"


def download_file(url: str, dest: Path) -> None:
    """Download a file from a URL with progress reporting."""
    print(f"Downloading from {url} ...")

    def report_progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 // total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  {mb_downloaded:.1f} / {mb_total:.1f} MB ({percent}%)", end="", flush=True)

    urllib.request.urlretrieve(url, str(dest), reporthook=report_progress)
    print()


def extract_and_flatten(archive_path: Path, dest_dir: Path) -> None:
    """Extract a tar.gz file, flattening all files into the destination directory."""
    print(f"Extracting to {dest_dir}/ ...")
    dest_dir.mkdir(exist_ok=True)
    count = 0
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            filename = Path(member.name).name
            if filename.startswith("._"):
                continue
            member.name = filename
            tf.extract(member, dest_dir)
            count += 1
    print(f"  Extracted {count} files.")


def main() -> None:
    """Download and extract the uncapped SemMedDB data."""
    archive_path = Path(ARCHIVE_FILENAME)

    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        print(f"Data directory '{OUTPUT_DIR}/' already exists and is not empty. Skipping download.")
        print("Delete the directory and re-run this script to re-download.")
        return

    download_file(S3_URL, archive_path)
    extract_and_flatten(archive_path, OUTPUT_DIR)

    archive_path.unlink()
    print(f"Done. Removed {ARCHIVE_FILENAME}.")
    print(f"Data files are in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
