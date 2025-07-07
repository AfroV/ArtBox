#!/usr/bin/env python3
"""
Real NFT Data Fetcher
Integrates with actual NFT APIs to fetch real wallet data
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import base64

class RealNFTFetcher:
    def __init__(self, api_manager=None):
        self.api_manager = api_manager
        self.rate_limits = {
            "alchemy": {"requests_per_second": 5, "last_request": 0},
            "moralis": {"requests_per_second": 25, "last_request": 0},
            "opensea": {"requests_per_second": 4, "last_request": 0},
            "nftport": {"requests_per_second": 1, "last_request": 0},
            "center": {"requests_per_second": 10, "last_request": 0}
        }
        
        self.api_keys = {}
        if api_manager:
            self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from the manager"""
        try:
            config_dir = Path.home() / ".nft-artbox"
            secure_file = config_dir / "secure_keys.enc"
            
            if secure_file.exists():
                with open(secure_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = base64.b64decode(encrypted_data)
                self.api_keys = json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error loading API keys: {e}")
            self.api_keys = {}
    
    def respect_rate_limit(self, api_name):
        """Ensure we respect API rate limits"""
        if api_name not in self.rate_limits:
            return
        
        rate_info = self.rate_limits[api_name]
        min_interval = 1.0 / rate_info["requests_per_second"]
        
        time_since_last = time.time() - rate_info["last_request"]
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        rate_info["last_request"] = time.time()
    
    def fetch_nfts_alchemy(self, wallet_address):
        """Fetch NFTs using Alchemy API"""
        if "alchemy" not in self.api_keys:
            raise Exception("Alchemy API key not configured")
        
        self.respect_rate_limit("alchemy")
        
        api_key = self.api_keys["alchemy"]
        url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getNFTsForOwner"
        
        params = {
            "owner": wallet_address,
            "withMetadata": "true",
            "pageSize": "100"
        }
        
        headers = {"Accept": "application/json"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        print("DEBUG: Requesting URL:", response.url)
        print("DEBUG: API Response Text:", response.text)
        
        data = response.json()
        return self.normalize_alchemy_response(data)
    
    def fetch_nfts_moralis(self, wallet_address):
        """Fetch NFTs using Moralis API"""
        if "moralis" not in self.api_keys:
            raise Exception("Moralis API key not configured")
        
        self.respect_rate_limit("moralis")
        
        url = f"https://deep-index.moralis.io/api/v2.2/{wallet_address}/nft"
        
        params = {
            "chain": "eth",
            "format": "decimal",
            "normalizeMetadata": "true",
            "limit": "100"
        }
        
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.api_keys["moralis"]
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self.normalize_moralis_response(data)
    
    def fetch_nfts_opensea(self, wallet_address):
        """Fetch NFTs using OpenSea API"""
        if "opensea" not in self.api_keys:
            raise Exception("OpenSea API key not configured")
        
        self.respect_rate_limit("opensea")
        
        url = f"https://api.opensea.io/api/v2/chain/ethereum/account/{wallet_address}/nfts"
        
        headers = {
            "Accept": "application/json",
            "X-API-KEY": self.api_keys["opensea"]
        }
        
        params = {"limit": "200"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self.normalize_opensea_response(data)
    
    def normalize_alchemy_response(self, data):
        """Normalize Alchemy API response to standard format"""
        nfts = []
        
        for nft in data.get("ownedNfts", []):
            try:
                contract = nft.get("contract", {})
                contract_address = contract.get("address", "")
                
                metadata = nft.get("metadata", {})
                raw_metadata = nft.get("rawMetadata", {})
                
                image_url = ""
                if metadata.get("image"):
                    image_url = metadata["image"]
                elif raw_metadata.get("image"):
                    image_url = raw_metadata["image"]
                
                if image_url.startswith("ipfs://"):
                    image_url = f"https://ipfs.io/ipfs/{image_url[7:]}"
                
                normalized_nft = {
                    "contract": {
                        "address": contract_address,
                        "name": contract.get("name", "Unknown"),
                        "symbol": contract.get("symbol", "")
                    },
                    "tokenId": nft.get("tokenId", ""),
                    "title": metadata.get("name", f"Token #{nft.get('tokenId', '')}"),
                    "description": metadata.get("description", ""),
                    "media": [{"gateway": image_url}] if image_url else [],
                    "metadata": {
                        "name": metadata.get("name", ""),
                        "description": metadata.get("description", ""),
                        "image": image_url,
                        "attributes": metadata.get("attributes", []),
                        "external_url": metadata.get("external_url", "")
                    },
                    "timeLastUpdated": datetime.now().isoformat(),
                    "source_api": "alchemy"
                }
                
                nfts.append(normalized_nft)
                
            except Exception as e:
                print(f"Error normalizing Alchemy NFT: {e}")
                continue
        
        return nfts
    
    def normalize_moralis_response(self, data):
        """Normalize Moralis API response to standard format"""
        nfts = []
        
        for nft in data.get("result", []):
            try:
                metadata = nft.get("normalized_metadata", {}) or nft.get("metadata", {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                image_url = metadata.get("image", "")
                if image_url.startswith("ipfs://"):
                    image_url = f"https://ipfs.io/ipfs/{image_url[7:]}"
                
                normalized_nft = {
                    "contract": {
                        "address": nft.get("token_address", ""),
                        "name": nft.get("name", "Unknown"),
                        "symbol": nft.get("symbol", "")
                    },
                    "tokenId": nft.get("token_id", ""),
                    "title": metadata.get("name", f"Token #{nft.get('token_id', '')}"),
                    "description": metadata.get("description", ""),
                    "media": [{"gateway": image_url}] if image_url else [],
                    "metadata": {
                        "name": metadata.get("name", ""),
                        "description": metadata.get("description", ""),
                        "image": image_url,
                        "attributes": metadata.get("attributes", []),
                        "external_url": metadata.get("external_url", "")
                    },
                    "timeLastUpdated": datetime.now().isoformat(),
                    "source_api": "moralis"
                }
                
                nfts.append(normalized_nft)
                
            except Exception as e:
                print(f"Error normalizing Moralis NFT: {e}")
                continue
        
        return nfts
    
    def normalize_opensea_response(self, data):
        """Normalize OpenSea API response to standard format"""
        nfts = []
        
        for nft in data.get("nfts", []):
            try:
                contract = nft.get("contract", "")
                metadata = nft.get("metadata", {}) or {}
                
                image_url = nft.get("image_url", "") or metadata.get("image", "")
                if image_url.startswith("ipfs://"):
                    image_url = f"https://ipfs.io/ipfs/{image_url[7:]}"
                
                normalized_nft = {
                    "contract": {
                        "address": contract,
                        "name": nft.get("collection", "Unknown"),
                        "symbol": ""
                    },
                    "tokenId": nft.get("identifier", ""),
                    "title": nft.get("name", f"Token #{nft.get('identifier', '')}"),
                    "description": nft.get("description", ""),
                    "media": [{"gateway": image_url}] if image_url else [],
                    "metadata": {
                        "name": nft.get("name", ""),
                        "description": nft.get("description", ""),
                        "image": image_url,
                        "attributes": nft.get("traits", []),
                        "external_url": metadata.get("external_url", "")
                    },
                    "timeLastUpdated": datetime.now().isoformat(),
                    "source_api": "opensea"
                }
                
                nfts.append(normalized_nft)
                
            except Exception as e:
                print(f"Error normalizing OpenSea NFT: {e}")
                continue
        
        return nfts
    
    def fetch_nfts_with_fallback(self, wallet_address, primary_api="alchemy", fallback_apis=None):
        """Fetch NFTs with automatic fallback to other APIs"""
        if fallback_apis is None:
            fallback_apis = ["moralis", "opensea", "nftport", "center"]
        
        apis_to_try = [primary_api] + [api for api in fallback_apis if api != primary_api]
        
        for api_name in apis_to_try:
            try:
                if api_name not in self.api_keys:
                    print(f"No API key configured for {api_name}, skipping...")
                    continue
                
                print(f"Trying to fetch NFTs using {api_name}...")
                
                if api_name == "alchemy":
                    nfts = self.fetch_nfts_alchemy(wallet_address)
                elif api_name == "moralis":
                    nfts = self.fetch_nfts_moralis(wallet_address)
                elif api_name == "opensea":
                    nfts = self.fetch_nfts_opensea(wallet_address)
                else:
                    continue
                
                if nfts:
                    print(f"Successfully fetched {len(nfts)} NFTs using {api_name}")
                    return nfts
                else:
                    print(f"No NFTs found using {api_name}")
                    
            except Exception as e:
                print(f"Error fetching from {api_name}: {e}")
                continue
        
        # If we get here, all APIs failed
        raise Exception("All configured APIs failed to fetch NFT data")
    
    def resolve_ens_name(self, ens_name):
        """Resolve ENS name to Ethereum address"""
        try:
            url = f"https://api.ensideas.com/ens/resolve/{ens_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("address")
        except Exception as e:
            print(f"Error resolving ENS name: {e}")
        
        return None
    
    def validate_ethereum_address(self, address):
        """Validate Ethereum address format"""
        if not address:
            return False
        
        if address.startswith('0x'):
            address = address[2:]
        
        if len(address) != 40:
            return False
        
        try:
            int(address, 16)
            return True
        except ValueError:
            return False

def main():
    """Demo the real NFT fetcher"""
    print("🔄 Testing Real NFT Fetcher...")
    
    fetcher = RealNFTFetcher()
    
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    try:
        nfts = fetcher.fetch_nfts_with_fallback(test_address)
        print(f"✅ Found {len(nfts)} NFTs")
        
        if nfts:
            print(f"Sample NFT: {nfts[0]['title']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Configure API keys first using the API Key Manager")

if __name__ == "__main__":
    main()