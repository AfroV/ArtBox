#!/usr/bin/env python3
"""
Enhanced IPFS ArtBox to NFT Viewer Bridge
Converts ArtBox cached data to NFT Viewer format with smart IPFS connectivity
"""

import sqlite3
import json
import os
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import logging
import subprocess
import platform
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced IPFS Connection Manager for CLI
class EnhancedIPFSManager:
    def __init__(self):
        self.ipfs_api = "http://127.0.0.1:5001"
        self.ipfs_gateway = "http://127.0.0.1:8080/ipfs/"
        self.is_connected = False
        
    def check_ipfs_status(self) -> bool:
        """Check if IPFS is running"""
        try:
            response = requests.get(f"{self.ipfs_api}/api/v0/id", timeout=3)
            if response.status_code == 200:
                self.is_connected = True
                peer_info = response.json()
                logger.info(f"✅ IPFS Connected - Peer ID: {peer_info.get('ID', 'Unknown')[:12]}...")
                return True
        except requests.exceptions.ConnectionError:
            logger.warning("❌ IPFS not running - Connection refused")
        except requests.exceptions.Timeout:
            logger.warning("⏱️ IPFS connection timeout")
        except Exception as e:
            logger.warning(f"❌ IPFS connection error: {e}")
        
        self.is_connected = False
        return False
    
    def ensure_connected(self) -> bool:
        """Ensure IPFS is connected, try to start if not"""
        if self.check_ipfs_status():
            return True
        
        logger.info("🔄 Attempting to start IPFS automatically...")
        
        # Try different connection methods
        if self._try_start_ipfs():
            time.sleep(3)  # Wait for startup
            return self.check_ipfs_status()
        
        return False
    
    def _try_start_ipfs(self) -> bool:
        """Try to start IPFS using various methods"""
        methods = [
            ("systemctl user", ["systemctl", "--user", "start", "ipfs"]),
            ("systemctl system", ["sudo", "systemctl", "start", "ipfs"]),
            ("direct daemon", ["ipfs", "daemon"])
        ]
        
        for method_name, cmd in methods:
            try:
                logger.info(f"🔧 Trying {method_name}...")
                if method_name == "direct daemon":
                    # For daemon, start in background
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE, text=True)
                    time.sleep(2)
                    if process.poll() is None:  # Still running
                        logger.info(f"✅ Started IPFS with {method_name}")
                        return True
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info(f"✅ Started IPFS with {method_name}")
                        return True
            except subprocess.TimeoutExpired:
                logger.warning(f"⏱️ {method_name} timed out")
            except FileNotFoundError:
                logger.debug(f"🔍 {method_name} command not found")
            except Exception as e:
                logger.debug(f"❌ {method_name} failed: {e}")
        
        return False
    
    def show_manual_instructions(self):
        """Show manual IPFS start instructions"""
        logger.error("🚀 Could not start IPFS automatically")
        logger.info("Please start IPFS manually:")
        logger.info("🐧 Linux: sudo systemctl start ipfs")
        logger.info("🍎 macOS: brew services start ipfs")
        logger.info("🪟 Windows: ipfs.exe daemon")
        logger.info("💿 Not installed? Visit: https://docs.ipfs.io/install/")

class ArtBoxViewerBridge:
    def __init__(self, artbox_cache_db=None, viewer_output_dir=None):
        self.artbox_cache_db = artbox_cache_db or Path.home() / "ipfs-artbox" / "cache.db"
        self.viewer_output_dir = Path(viewer_output_dir or Path.home() / "nft-metadata")
        self.viewer_output_dir.mkdir(exist_ok=True)
        
        # Enhanced IPFS manager
        self.ipfs_manager = EnhancedIPFSManager()
        
        # Rate limiting for API calls
        self.last_api_call = 0
        self.api_delay = 0.5
        
    def connect_to_artbox_cache(self) -> sqlite3.Connection:
        """Connect to ArtBox cache database"""
        if not self.artbox_cache_db.exists():
            raise FileNotFoundError(f"ArtBox cache database not found: {self.artbox_cache_db}")
        
        return sqlite3.connect(self.artbox_cache_db)
    
    def get_cached_nfts(self) -> List[Dict]:
        """Retrieve all cached NFTs from ArtBox database"""
        try:
            conn = self.connect_to_artbox_cache()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT contract_address, token_id, metadata, cached_at 
                FROM nft_cache 
                ORDER BY cached_at DESC
            """)
            
            cached_nfts = []
            for row in cursor.fetchall():
                contract_address, token_id, metadata_json, cached_at = row
                try:
                    metadata = json.loads(metadata_json)
                    cached_nfts.append({
                        'contract_address': contract_address,
                        'token_id': token_id,
                        'metadata': metadata,
                        'cached_at': cached_at
                    })
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON for {contract_address}#{token_id}")
                    continue
            
            conn.close()
            return cached_nfts
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return []
    
    def download_and_pin_image(self, image_url: str, nft_name: str) -> Optional[str]:
        """Download image and pin to IPFS with enhanced error handling"""
        if not self.ipfs_manager.is_connected:
            logger.warning("⚠️ IPFS not connected - cannot pin images")
            return None
        
        try:
            # Rate limiting
            now = time.time()
            if now - self.last_api_call < self.api_delay:
                time.sleep(self.api_delay - (now - self.last_api_call))
            
            # Handle IPFS URLs
            if image_url.startswith('ipfs://'):
                ipfs_hash = image_url.replace('ipfs://', '')
                # Pin existing hash with retry
                for attempt in range(3):
                    try:
                        pin_response = requests.post(
                            f"{self.ipfs_manager.ipfs_api}/api/v0/pin/add",
                            params={'arg': ipfs_hash},
                            timeout=10
                        )
                        if pin_response.status_code == 200:
                            self.last_api_call = time.time()
                            logger.info(f"📌 Pinned existing IPFS hash: {ipfs_hash[:20]}...")
                            return ipfs_hash
                    except Exception as e:
                        if attempt == 2:  # Last attempt
                            logger.warning(f"Failed to pin existing hash {ipfs_hash}: {e}")
                        time.sleep(1)
                return None
            
            # Download and pin new image
            logger.info(f"📥 Downloading image for {nft_name}...")
            
            # Download with retry
            for attempt in range(3):
                try:
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt == 2:
                        logger.warning(f"Failed to download image {image_url}: {e}")
                        return None
                    time.sleep(1)
            
            # Add to IPFS with retry
            for attempt in range(3):
                try:
                    files = {'file': ('image', response.content)}
                    ipfs_response = requests.post(
                        f"{self.ipfs_manager.ipfs_api}/api/v0/add",
                        files=files,
                        timeout=30
                    )
                    
                    if ipfs_response.status_code == 200:
                        result = ipfs_response.json()
                        ipfs_hash = result['Hash']
                        
                        # Pin the hash
                        pin_response = requests.post(
                            f"{self.ipfs_manager.ipfs_api}/api/v0/pin/add",
                            params={'arg': ipfs_hash},
                            timeout=10
                        )
                        
                        self.last_api_call = time.time()
                        if pin_response.status_code == 200:
                            logger.info(f"✅ Downloaded and pinned: {ipfs_hash[:20]}...")
                            return ipfs_hash
                        else:
                            logger.warning(f"Failed to pin uploaded hash: {ipfs_hash}")
                            return ipfs_hash  # Return hash even if pinning failed
                
                except Exception as e:
                    if attempt == 2:
                        logger.warning(f"Failed to upload image to IPFS: {e}")
                    time.sleep(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading/pinning image {image_url}: {e}")
            return None
    
    def convert_to_viewer_format(self, nft_data: Dict, image_hash: str = None) -> Dict:
        """Convert NFT data to enhanced viewer format"""
        metadata = nft_data.get('metadata', {})
        
        # Extract or download/pin image hash
        if not image_hash and 'image' in metadata:
            image_url = metadata['image']
            if image_url.startswith('ipfs://'):
                image_hash = image_url.replace('ipfs://', '')
            elif '/ipfs/' in image_url:
                image_hash = image_url.split('/ipfs/')[-1]
            else:
                # Try to download and pin
                image_hash = self.download_and_pin_image(
                    image_url,
                    metadata.get('name', f"Token {nft_data.get('token_id', '')}")
                )
        
        # Create enhanced viewer item
        viewer_item = {
            "name": metadata.get('name', f"Token #{nft_data.get('token_id', '')}"),
            "description": metadata.get('description', ''),
            "image": image_hash or '',
            "token_id": str(nft_data.get('token_id', '')),
            "collection": nft_data.get('contract_address', ''),
            "attributes": metadata.get('attributes', []),
            # Enhanced metadata
            "enhanced_bridge_info": {
                "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "original_cached_at": nft_data.get('cached_at', ''),
                "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                "ipfs_connected": self.ipfs_manager.is_connected,
                "bridge_version": "Enhanced 2.0"
            }
        }
        
        return viewer_item
    
    def sync_all_cached_collections(self) -> List[str]:
        """Sync all collections from ArtBox cache to enhanced viewer format"""
        # Ensure IPFS connection
        if not self.ipfs_manager.ensure_connected():
            logger.warning("⚠️ IPFS not available - proceeding without image pinning")
            self.ipfs_manager.show_manual_instructions()
        
        cached_nfts = self.get_cached_nfts()
        
        if not cached_nfts:
            logger.warning("No cached NFTs found")
            return []
        
        logger.info(f"📊 Found {len(cached_nfts)} cached NFTs")
        
        # Group by contract address
        collections = {}
        for nft in cached_nfts:
            contract = nft['contract_address']
            if contract not in collections:
                collections[contract] = []
            collections[contract].append(nft)
        
        output_files = []
        
        for contract_address, nfts in collections.items():
            logger.info(f"🔄 Processing enhanced collection: {contract_address} ({len(nfts)} NFTs)")
            
            collection_items = []
            
            for i, nft_data in enumerate(nfts):
                try:
                    logger.info(f"📝 Processing NFT {i+1}/{len(nfts)}: {contract_address}#{nft_data.get('token_id', '')}")
                    
                    # Convert to enhanced viewer format (includes image pinning if IPFS available)
                    viewer_item = self.convert_to_viewer_format(nft_data)
                    collection_items.append(viewer_item)
                    
                except Exception as e:
                    logger.error(f"Error processing NFT {nft_data.get('token_id', '')}: {e}")
                    continue
            
            # Save enhanced collection file
            if collection_items:
                contract_suffix = contract_address[-8:] if len(contract_address) >= 8 else contract_address
                output_file = self.viewer_output_dir / f"enhanced_collection_{contract_suffix}.json"
                
                # Add collection-level enhanced metadata
                enhanced_collection_data = {
                    "enhanced_collection_info": {
                        "contract_address": contract_address,
                        "total_items": len(collection_items),
                        "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                        "ipfs_connected_during_processing": self.ipfs_manager.is_connected,
                        "bridge_tool": "Enhanced ArtBox-Viewer Bridge",
                        "bridge_version": "2.0-Enhanced"
                    },
                    "items": collection_items
                }
                
                with open(output_file, 'w') as f:
                    json.dump(enhanced_collection_data, f, indent=2)
                
                logger.info(f"✅ Saved {len(collection_items)} enhanced NFTs to {output_file}")
                output_files.append(str(output_file))
        
        return output_files
    
    def generate_viewer_config(self, collection_files: List[str]) -> str:
        """Generate enhanced viewer configuration file"""
        collections = []
        
        for file_path in collection_files:
            file_name = Path(file_path).stem
            collection_name = file_name.replace("enhanced_collection_", "").replace("_", " ").title()
            
            collections.append({
                "name": f"Enhanced Collection {collection_name}",
                "metadata_file": file_path,
                "enhanced_features": True
            })
        
        enhanced_config = {
            "enhanced_viewer_info": {
                "version": "Enhanced 2.0",
                "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                "total_collections": len(collections)
            },
            "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
            "collections": collections,
            "display": {
                "interval": 10,
                "random_order": True,
                "show_metadata": True,
                "show_enhanced_info": True,
                "transition_duration": 0.5,
                "fullscreen": True
            },
            "cache": {
                "max_images_in_memory": 5,
                "preload_next": True,
                "enhanced_caching": True
            },
            "web_interface": {
                "enabled": True,
                "port": 5000,
                "host": "0.0.0.0",
                "enhanced_features": True
            },
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "error_image_path": None,
            "enhanced_features": {
                "auto_ipfs_connection": True,
                "smart_pinning": True,
                "error_recovery": True,
                "progress_tracking": True
            }
        }
        
        config_file = self.viewer_output_dir / "enhanced_viewer_config.json"
        with open(config_file, 'w') as f:
            json.dump(enhanced_config, f, indent=2)
        
        logger.info(f"✅ Generated enhanced viewer config: {config_file}")
        return str(config_file)
    
    def create_sample_data(self) -> str:
        """Create enhanced sample NFT data if no ArtBox cache exists"""
        logger.info("🎨 Creating enhanced sample NFT data for testing...")
        
        enhanced_sample_nfts = {
            "enhanced_collection_info": {
                "contract_address": "0xSampleEnhancedContract123456789",
                "total_items": 4,
                "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                "ipfs_connected_during_processing": self.ipfs_manager.is_connected,
                "bridge_tool": "Enhanced ArtBox-Viewer Bridge",
                "bridge_version": "2.0-Enhanced",
                "sample_data": True
            },
            "items": [
                {
                    "name": "Enhanced Sample NFT #1",
                    "description": "A beautiful enhanced digital artwork showcasing the power of smart IPFS connectivity and auto-connection features",
                    "image": "QmEnhancedSample1abcdefghijklmnopqrstuvwxyz1234567890",
                    "token_id": "1",
                    "collection": "Enhanced Sample Collection",
                    "attributes": [
                        {"trait_type": "Background", "value": "Smart Blue Gradient"},
                        {"trait_type": "Style", "value": "Enhanced Abstract"},
                        {"trait_type": "Rarity", "value": "Common"},
                        {"trait_type": "Enhanced Features", "value": "Auto-Connect"},
                        {"trait_type": "Bridge Version", "value": "2.0-Enhanced"}
                    ],
                    "enhanced_bridge_info": {
                        "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "original_cached_at": "",
                        "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                        "ipfs_connected": self.ipfs_manager.is_connected,
                        "bridge_version": "Enhanced 2.0",
                        "sample_data": True
                    }
                },
                {
                    "name": "Enhanced Sample NFT #2",
                    "description": "An artistic representation of enhanced digital ownership with smart IPFS management and creative expression",
                    "image": "QmEnhancedSample2abcdefghijklmnopqrstuvwxyz1234567890",
                    "token_id": "2",
                    "collection": "Enhanced Sample Collection",
                    "attributes": [
                        {"trait_type": "Background", "value": "Smart Red Sunset"},
                        {"trait_type": "Style", "value": "Enhanced Photorealistic"},
                        {"trait_type": "Rarity", "value": "Rare"},
                        {"trait_type": "Enhanced Features", "value": "Smart Pinning"},
                        {"trait_type": "Bridge Version", "value": "2.0-Enhanced"}
                    ],
                    "enhanced_bridge_info": {
                        "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "original_cached_at": "",
                        "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                        "ipfs_connected": self.ipfs_manager.is_connected,
                        "bridge_version": "Enhanced 2.0",
                        "sample_data": True
                    }
                },
                {
                    "name": "Enhanced Sample NFT #3",
                    "description": "A demonstration of enhanced NFT viewing technology with smart metadata display and auto-connectivity",
                    "image": "QmEnhancedSample3abcdefghijklmnopqrstuvwxyz1234567890",
                    "token_id": "3",
                    "collection": "Enhanced Sample Collection",
                    "attributes": [
                        {"trait_type": "Background", "value": "Smart Purple Space"},
                        {"trait_type": "Style", "value": "Enhanced Minimalist"},
                        {"trait_type": "Rarity", "value": "Epic"},
                        {"trait_type": "Enhanced Features", "value": "Error Recovery"},
                        {"trait_type": "Bridge Version", "value": "2.0-Enhanced"}
                    ],
                    "enhanced_bridge_info": {
                        "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "original_cached_at": "",
                        "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                        "ipfs_connected": self.ipfs_manager.is_connected,
                        "bridge_version": "Enhanced 2.0",
                        "sample_data": True
                    }
                },
                {
                    "name": "Enhanced Sample NFT #4",
                    "description": "A showcase of enhanced bridge capabilities featuring smart IPFS integration and automated connectivity management",
                    "image": "QmEnhancedSample4abcdefghijklmnopqrstuvwxyz1234567890",
                    "token_id": "4",
                    "collection": "Enhanced Sample Collection",
                    "attributes": [
                        {"trait_type": "Background", "value": "Smart Golden Aurora"},
                        {"trait_type": "Style", "value": "Enhanced Futuristic"},
                        {"trait_type": "Rarity", "value": "Legendary"},
                        {"trait_type": "Enhanced Features", "value": "All Features"},
                        {"trait_type": "Bridge Version", "value": "2.0-Enhanced"}
                    ],
                    "enhanced_bridge_info": {
                        "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "original_cached_at": "",
                        "ipfs_gateway": self.ipfs_manager.ipfs_gateway,
                        "ipfs_connected": self.ipfs_manager.is_connected,
                        "bridge_version": "Enhanced 2.0",
                        "sample_data": True
                    }
                }
            ]
        }
        
        # Save enhanced sample data
        sample_file = self.viewer_output_dir / "enhanced_sample_collection.json"
        with open(sample_file, 'w') as f:
            json.dump(enhanced_sample_nfts, f, indent=2)
        
        logger.info(f"✅ Created enhanced sample collection: {sample_file}")
        return str(sample_file)
    
    def check_ipfs_running(self) -> bool:
        """Check if IPFS is running using enhanced manager"""
        return self.ipfs_manager.check_ipfs_status()

def main():
    parser = argparse.ArgumentParser(description='Enhanced ArtBox cache to NFT Viewer bridge')
    parser.add_argument('--cache-db', help='Path to ArtBox cache database')
    parser.add_argument('--output-dir', help='Output directory for viewer files')
    parser.add_argument('--sync-all', action='store_true', help='Sync all cached collections with enhanced features')
    parser.add_argument('--create-sample', action='store_true', help='Create enhanced sample data for testing')
    parser.add_argument('--ensure-ipfs', action='store_true', help='Ensure IPFS is running before operations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bridge = ArtBoxViewerBridge(args.cache_db, args.output_dir)
    
    try:
        print("🌉 Enhanced ArtBox-Viewer Bridge v2.0")
        print("✨ Features: Smart IPFS connectivity, auto-retry, enhanced metadata")
        print()
        
        if args.ensure_ipfs:
            print("🔄 Ensuring IPFS connection...")
            if not bridge.ipfs_manager.ensure_connected():
                print("❌ Could not establish IPFS connection")
                bridge.ipfs_manager.show_manual_instructions()
                return 1
            print("✅ IPFS connection established")
            print()
        
        if args.create_sample:
            # Create enhanced sample data
            sample_file = bridge.create_sample_data()
            config_file = bridge.generate_viewer_config([sample_file])
            
            print("✅ Enhanced sample NFT data created!")
            print(f"📋 Enhanced config file: {config_file}")
            print("\n🎯 Next steps:")
            print("1. Start Enhanced NFT Slideshow Viewer")
            print("2. Use Enhanced NFT Collector to fetch real NFTs")
            print("3. Run enhanced sync again to include real data")
            print("\n✨ Enhanced features available:")
            print("  • Smart IPFS auto-connection")
            print("  • Enhanced metadata processing")
            print("  • Error recovery mechanisms")
            print("  • Progress tracking")
            
        elif args.sync_all:
            # Check IPFS status
            ipfs_status = bridge.check_ipfs_running()
            if not ipfs_status:
                print("⚠️  Warning: IPFS not running. Enhanced features will be limited.")
                print("   Start IPFS with: sudo systemctl start ipfs")
                print("   Or use --ensure-ipfs flag for auto-connection")
            else:
                print("✅ IPFS connected and ready for enhanced operations")
            print()
            
            # Sync all cached collections with enhanced features
            collection_files = bridge.sync_all_cached_collections()
            
            if collection_files:
                config_file = bridge.generate_viewer_config(collection_files)
                
                print(f"✅ Enhanced sync complete: {len(collection_files)} collections processed")
                print(f"📋 Enhanced config file: {config_file}")
                print("\n🎯 Next steps:")
                print("1. Start Enhanced NFT Slideshow Viewer")
                print("2. Use enhanced keyboard controls (Space, M, R, Q)")
                print("3. Access enhanced web control at http://localhost:5000")
                print("\n✨ Enhanced features in your collections:")
                print("  • Smart IPFS connectivity information")
                print("  • Enhanced metadata with processing timestamps")
                print("  • Auto-connection support for future operations")
                print("  • Error recovery and retry mechanisms")
                print("  • Improved caching and performance")
                
            else:
                print("❌ No NFT collections found in ArtBox cache")
                print("\n💡 Try:")
                print("1. Use Enhanced NFT Collector to fetch NFTs first")
                print("2. Or run with --create-sample for enhanced test data")
                print("3. Check that ~/ipfs-artbox/cache.db exists")
        
        else:
            print("🌉 Enhanced ArtBox-Viewer Bridge v2.0")
            print("\nUsage:")
            print("  --sync-all        Sync all cached NFTs to enhanced viewer format")
            print("  --create-sample   Create enhanced sample data for testing")
            print("  --ensure-ipfs     Ensure IPFS is running before operations")
            print("  --verbose         Show detailed output")
            print("\nEnhanced Examples:")
            print("  python3 enhanced_bridge_script.py --sync-all --ensure-ipfs")
            print("  python3 enhanced_bridge_script.py --create-sample")
            print("\n✨ Enhanced Features:")
            print("  • Smart IPFS auto-connection and management")
            print("  • Enhanced error handling and retry mechanisms")
            print("  • Improved metadata processing and caching")
            print("  • Progress tracking and status reporting")
            print("  • Backward compatibility with standard viewers")
            
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n💡 Make sure to:")
        print("1. Use Enhanced NFT Collector to fetch some NFTs first")
        print("2. Check that ~/ipfs-artbox/cache.db exists")
        print("3. Or use --create-sample for enhanced test data")
        print("4. Use --ensure-ipfs for automatic IPFS connection")
        return 1
    except Exception as e:
        logger.error(f"Enhanced bridge error: {e}")
        print(f"\n❌ Error occurred: {e}")
        print("\n💡 Try:")
        print("1. Run with --verbose for detailed output")
        print("2. Use --ensure-ipfs for automatic IPFS connection")
        print("3. Check IPFS status manually")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())