#!/usr/bin/env python3
"""
NFT System Core Library - v2.0 (Refactored)
Handles all backend logic: IPFS, Database, API Fetching, and Secure Key Management.
"""

import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path
import base64
import requests
import psutil

# Ensure cryptography is installed: pip install cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("Cryptography library not found. Please run: pip install cryptography")
    Fernet = None

# --- Configuration Manager ---
class ConfigManager:
    def __init__(self, config_dir: Path):
        self.config_path = config_dir / "config.json"
        self.defaults = {
            "ipfs_api": "http://127.0.0.1:5001",
            "ipfs_gateway": "http://127.0.0.1:8080/ipfs/",
            "primary_api": "alchemy",
            "test_wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "gateway_preference": "auto",
            "custom_gateway": ""
        }
        self.config = self.load()

    def load(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                try:
                    loaded_config = json.load(f)
                    # Ensure all default keys exist
                    for key, value in self.defaults.items():
                        loaded_config.setdefault(key, value)
                    return loaded_config
                except json.JSONDecodeError:
                    return self.defaults.copy()
        return self.defaults.copy()

    def save(self):
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default=None):
        """Get a config value with optional default"""
        if default is not None:
            return self.config.get(key, default)
        return self.config.get(key, self.defaults.get(key))

    def set(self, key: str, value):
        self.config[key] = value
        self.save()

# --- Database Manager ---
class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT NOT NULL,
                token_id TEXT NOT NULL,
                title TEXT,
                description TEXT,
                image_url TEXT,
                image_hash TEXT,
                metadata TEXT,
                source_api TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contract_address, token_id)
            )
        ''')
        self.conn.commit()

    def cache_nfts(self, nfts: list):
        cursor = self.conn.cursor()
        for nft in nfts:
            metadata_str = json.dumps(nft.get('metadata', {}))
            
            # Extract image URL properly from media array or metadata
            image_url = ''
            media = nft.get('media', [])
            if media and len(media) > 0:
                image_url = media[0].get('gateway', '')
            
            # If no image in media, try metadata
            if not image_url:
                metadata = nft.get('metadata', {})
                if isinstance(metadata, dict):
                    image_url = metadata.get('image', '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO nfts 
                (contract_address, token_id, title, description, image_url, metadata, source_api)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                nft.get('contract', {}).get('address', ''),
                nft.get('tokenId', ''),
                nft.get('title', 'Untitled'),
                nft.get('description', ''),
                image_url,  # Store the proper image URL
                metadata_str,
                nft.get('source_api', 'unknown')
            ))
        self.conn.commit()
    def get_all_nfts(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nfts ORDER BY cached_at DESC")
        rows = cursor.fetchall()
        # Convert sqlite3.Row to dict
        return [dict(row) for row in rows]

    def close(self):
        if self.conn:
            self.conn.close()


# --- Secure API Key Manager (Logic Only) ---
class SecureAPIKeyManager:
    def __init__(self, secure_dir: Path):
        if not Fernet:
            raise ImportError("Cryptography library is required for secure key storage.")
        
        self.secure_file = secure_dir / "api_keys.enc"
        # In a real-world scenario, this salt should be stored securely,
        # and the password prompted from the user. For this headless system,
        # we use a fixed salt and a hardcoded "password" for simplicity.
        self.salt = b'nft-system-salt'
        self.password = b'raspberry-pi-nft-project'
        self.fernet = self._get_fernet_instance()

    def _get_fernet_instance(self) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return Fernet(key)

    def save_keys(self, api_keys: dict):
        keys_json = json.dumps(api_keys).encode('utf-8')
        encrypted_data = self.fernet.encrypt(keys_json)
        with open(self.secure_file, 'wb') as f:
            f.write(encrypted_data)
        os.chmod(self.secure_file, 0o600)

    def load_keys(self) -> dict:
        if not self.secure_file.exists():
            return {}
        try:
            with open(self.secure_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            # Handle cases like changed password or corrupted file
            return {}


# --- Unified IPFS Manager ---
# --- Unified IPFS Manager ---
class IPFSManager:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.is_connected = False
        # Add the missing ipfs_gateway attribute
        self.ipfs_gateway = "https://ipfs.io/ipfs/"  # Default public gateway

    def check_status(self) -> bool:
        try:
            response = requests.post(f"{self.api_url}/api/v0/id", timeout=3)
            self.is_connected = response.status_code == 200
            return self.is_connected
        except requests.exceptions.RequestException:
            self.is_connected = False
            return False

    def ensure_running(self) -> bool:
        if self.check_status():
            return True
        
        # Check if process is already running but unresponsive
        for proc in psutil.process_iter(['name', 'cmdline']):
            if 'ipfs' in proc.info['name'] and 'daemon' in proc.info.get('cmdline', []):
                return False # Running but not responding, needs a restart

        # Try to start the daemon
        try:
            subprocess.Popen(["ipfs", "daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5) # Give it time to start
            return self.check_status()
        except FileNotFoundError:
            return False # IPFS not installed
        except Exception:
            return False

    def pin_hash(self, ipfs_hash: str) -> bool:
        if not self.is_connected:
            return False
        try:
            response = requests.post(f"{self.api_url}/api/v0/pin/add", params={'arg': ipfs_hash}, timeout=30)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def add_file(self, file_path: Path) -> (str | None):
        if not self.is_connected or not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            files = {'file': f}
            try:
                response = requests.post(f"{self.api_url}/api/v0/add", files=files, timeout=60)
                if response.status_code == 200:
                    return response.json()['Hash']
            except requests.exceptions.RequestException:
                return None
        return None


# --- Real NFT Fetcher ---
class RealNFTFetcher:
    def __init__(self, api_key_manager: SecureAPIKeyManager):
        self.api_manager = api_key_manager
        self.api_keys = self.api_manager.load_keys()
        self.supported_apis = ["alchemy", "moralis", "opensea"]

    def fetch_nfts(self, wallet_address: str, primary_api: str) -> (list | None):
        apis_to_try = [primary_api] + [api for api in self.supported_apis if api != primary_api]
        
        for api in apis_to_try:
            if api in self.api_keys:
                try:
                    if api == "alchemy":
                        return self._fetch_alchemy(wallet_address)
                    # Add other API fetch methods here...
                except Exception as e:
                    print(f"Failed to fetch from {api}: {e}")
        return None

    def _fetch_alchemy(self, wallet_address):
        api_key = self.api_keys["alchemy"]
        url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getNFTsForOwner"
        params = {"owner": wallet_address, "withMetadata": "true", "pageSize": "100"}
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return self._normalize_alchemy(data)

    def _normalize_alchemy(self, data):
        nfts = []
        for nft in data.get("ownedNfts", []):
            image_url = (nft.get('metadata', {}) or {}).get('image', '')
            if image_url.startswith("ipfs://"):
                image_url = f"https://ipfs.io/ipfs/{image_url.replace('ipfs://', '')}"
            
            nfts.append({
                "contract": {"address": nft.get("contract", {}).get("address")},
                "tokenId": nft.get("tokenId"),
                "title": nft.get("title", "Untitled"),
                "description": nft.get('metadata', {}).get('description', ''),
                "media": [{"gateway": image_url}],
                "metadata": nft.get('metadata', {}),
                "source_api": "alchemy"
            })
        return nfts