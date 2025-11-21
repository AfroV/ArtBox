#!/usr/bin/env python3
"""
XCOPY FINAL – short, complete, never stuck, with --workers support
"""

import csv
import json
import re
import time
from pathlib import Path
import requests
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

class XCOPYDownloader:
    def __init__(self, output_dir="ipfs_backup"):
        self.files_dir = Path(output_dir) / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = set()
        self.lock = Lock()
        self.progress_file = Path(output_dir) / "download_progress.json"
        self.session = requests.Session()
        # Match valid IPFS CIDs: CIDv0 (Qm...) or CIDv1 (baf..., bae..., etc)
        # CIDv0: Qm + 44 base58 chars (total 46)
        # CIDv1: typically starts with 'baf' in base32
        self.cid_pattern = re.compile(r'(?:https?://[^/\s]*ipfs[^/\s]*/(?:ipfs/)?|ipfs://)?(?:(Qm[a-zA-Z0-9]{44})|(baf[a-z0-9]{50,}))', re.I)
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            try:
                self.downloaded = set(json.load(open(self.progress_file)).get("downloaded", []))
                print(f"Progress loaded – {len(self.downloaded)} files already done")
            except: pass

    def _save_progress(self):
        json.dump({"downloaded": list(self.downloaded)}, open(self.progress_file, "w"), indent=2)

    def _download(self, cid):
        url = f"http://127.0.0.1:8080/ipfs/{cid}"
        print(f"  → {cid[:20]}...", end="", flush=True)
        for _ in range(40):                                    # ~13 minutes max – more than enough
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 1000:
                    print(f" SUCCESS ({len(r.content)/1048576:.2f} MB)")
                    return r.content
            except:
                pass
            print(".", end="", flush=True)
            time.sleep(20)
        print(" timeout – open this CID in IPFS Desktop to speed it up")
        return None

    def _exists(self, cid):
        return any((self.files_dir / f"{cid}{e}").exists() for e in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"])

    def _extract_all_cids(self, obj, parent_cid):
        """Recursively extract all IPFS CIDs from a JSON object"""
        cids = []

        if isinstance(obj, str):
            # Find all CIDs in this string
            for match in self.cid_pattern.finditer(obj):
                # Get the matched CID from either group 1 (Qm) or group 2 (baf)
                cid = match.group(1) or match.group(2)
                if cid and cid != parent_cid:  # Don't download the parent file again
                    cids.append(cid)
        elif isinstance(obj, dict):
            # Recursively search all values in the dictionary
            for value in obj.values():
                cids.extend(self._extract_all_cids(value, parent_cid))
        elif isinstance(obj, list):
            # Recursively search all items in the list
            for item in obj:
                cids.extend(self._extract_all_cids(item, parent_cid))

        return cids

    def download_cid(self, cid, name=""):
        cid = cid.strip()

        # Check if file already exists
        already_exists = self._exists(cid)

        if already_exists:
            # File exists - find it and check for nested hashes
            for ext in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"]:
                file_path = self.files_dir / f"{cid}{ext}"
                if file_path.exists():
                    # Process nested hashes for JSON and HTML files
                    if ext in [".json", ".html"]:
                        try:
                            data = file_path.read_bytes()
                            text_content = data.decode("utf-8", errors="ignore")

                            # For JSON, parse it; for HTML, just use the text content
                            if ext == ".json":
                                meta = json.loads(text_content)
                                nested_cids = self._extract_all_cids(meta, cid)
                            else:  # HTML
                                nested_cids = []
                                for match in self.cid_pattern.finditer(text_content):
                                    found_cid = match.group(1) or match.group(2)
                                    if found_cid and found_cid != cid:
                                        nested_cids.append(found_cid)

                            if nested_cids:
                                print(f"  ✓ Checking existing {ext[1:].upper()} {cid[:20]}... for nested hashes")
                                print(f"    → Found {len(nested_cids)} nested IPFS hash(es)")
                                for nested in nested_cids:
                                    if not self._exists(nested):
                                        print(f"      → Downloading: {nested[:20]}...")
                                        self.download_cid(nested)
                                    else:
                                        print(f"      ✓ Already exists: {nested[:20]}...")
                        except: pass
                    return True

        # File doesn't exist - download it
        data = self._download(cid)
        if not data:
            return False

        # Determine extension
        ext = ".bin"
        if data.startswith(b'<!DOCTYPE html'): ext = ".html"
        elif data.startswith(b'\x89PNG'): ext = ".png"
        elif data.startswith(b'\xff\xd8\xff'): ext = ".jpg"  # JPEG/JFIF/EXIF (all start with FFD8FF)
        elif data.startswith(b'GIF8'): ext = ".gif"
        elif len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP': ext = ".webp"
        elif len(data) >= 8 and data[4:8] in [b'ftyp', b'mdat', b'moov', b'wide']: ext = ".mp4"
        elif data.startswith(b'glTF'): ext = ".glb"
        else:
            try: json.loads(data); ext = ".json"
            except: pass

        # Save file
        (self.files_dir / f"{cid}{ext}").write_bytes(data)
        with self.lock:
            self.downloaded.add(cid)
            self._save_progress()

        # Check for nested hashes in newly downloaded JSON and HTML files
        if ext in [".json", ".html"]:
            try:
                text_content = data.decode("utf-8", errors="ignore")

                # For JSON, parse it; for HTML, just use the text content
                if ext == ".json":
                    meta = json.loads(text_content)
                    nested_cids = self._extract_all_cids(meta, cid)
                    file_name = meta.get('name', cid[:20]+'...')
                else:  # HTML
                    nested_cids = []
                    for match in self.cid_pattern.finditer(text_content):
                        found_cid = match.group(1) or match.group(2)
                        if found_cid and found_cid != cid:
                            nested_cids.append(found_cid)
                    file_name = cid[:20]+'...'

                if nested_cids:
                    print(f"    → Found {len(nested_cids)} nested IPFS hash(es) in {file_name}")
                    for nested in nested_cids:
                        if not self._exists(nested):
                            print(f"      → Downloading: {nested[:20]}...")
                            self.download_cid(nested)
                        else:
                            print(f"      ✓ Already exists: {nested[:20]}...")
            except: pass
        return True

    def run(self, csv_file, workers=1):
        items = []
        with open(csv_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = (row.get("cid") or row.get("CID") or "").strip()

                # If no direct CID column, try to extract from metadata_url or other URL fields
                if not cid:
                    metadata_url = (row.get("metadata_url") or row.get("metadataUrl") or "").strip()
                    if metadata_url:
                        match = self.cid_pattern.search(metadata_url)
                        if match:
                            cid = match.group(1) or match.group(2)

                if cid and cid not in ["See CSV","On-Chain","Arweave","--"]:
                    title = row.get("title") or row.get("name") or row.get("filename") or ""
                    items.append((title, cid))

        print(f"\nStarting download of {len(items)} items (workers = {workers})\n")

        def task(item):
            title, cid = item
            self.download_cid(cid, title)

        if workers == 1:
            for item in items:
                task(item)
        else:
            with ThreadPoolExecutor(max_workers=workers) as exe:
                for future in as_completed([exe.submit(task, i) for i in items]):
                    future.result()

        print("\n🎉 ALL DONE – your XCOPY archive is complete!")
        print(f"   Total unique files: {len(self.downloaded)}")
        print(f"   Folder: {self.files_dir.resolve()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backup completed!")
    parser.add_argument("csv", help="CSV file")
    parser.add_argument("--output", "-o", default="ipfs_backup", help="Output folder")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (1 is safest)")
    args = parser.parse_args()

    XCOPYDownloader(args.output).run(args.csv, workers=args.workers)