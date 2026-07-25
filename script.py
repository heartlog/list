import os
import sys
import zipfile
import json
from unittest.mock import MagicMock

# --- Path Configurations ---
ZIP_FILE = "plugin.video.cricfy-v1.3.1.zip"
EXTRACT_DIR = "extracted_addon"
# Use absolute paths to prevent any relative path confusion in os.path.join
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(BASE_DIR, EXTRACT_DIR, "plugin.video.cricfy")
LIB_DIR = os.path.join(ADDON_DIR, "lib")

def setup_environment():
    """Unzips the archive if not already extracted."""
    if not os.path.exists(ZIP_FILE):
        print(f"[-] Error: '{ZIP_FILE}' not found in the current directory.")
        sys.exit(1)
        
    if not os.path.exists(EXTRACT_DIR):
        print(f"[+] Extracting {ZIP_FILE}...")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
        print("[+] Extraction complete.")

def mock_kodi_modules():
    """Mocks Kodi runtime dependencies in memory with correct path handling."""
    def mock_translatePath(path):
        """Intercepts Kodi paths and returns the actual local Windows path."""
        # If it's a special Kodi path, or a mock object, force it to our actual directory
        if not isinstance(path, str) or path.startswith("special://"):
            return ADDON_DIR
        return path

    def mock_getAddonInfo(key):
        """Returns actual local paths when the add-on asks for its location."""
        if key in ['path', 'profile']:
            return ADDON_DIR
        return "1.3.1" # Mock version if requested

    # Setup core mock objects
    mock_xbmc = MagicMock()
    mock_xbmc.translatePath = mock_translatePath
    sys.modules['xbmc'] = mock_xbmc

    mock_xbmcvfs = MagicMock()
    mock_xbmcvfs.translatePath = mock_translatePath
    sys.modules['xbmcvfs'] = mock_xbmcvfs

    sys.modules['xbmcgui'] = MagicMock()
    sys.modules['xbmcplugin'] = MagicMock()
    sys.modules['routing'] = MagicMock()

    mock_addon = MagicMock()
    mock_addon.getSetting.return_value = ""
    mock_addon.getAddonInfo.side_effect = mock_getAddonInfo
    
    mock_xbmcaddon = MagicMock()
    mock_xbmcaddon.Addon.return_value = mock_addon
    sys.modules['xbmcaddon'] = mock_xbmcaddon

def fetch_provider_names():
    """Imports providers.py, retrieves the provider list, and saves it to a JSON file."""
    if ADDON_DIR not in sys.path:
        sys.path.insert(0, ADDON_DIR)
    if LIB_DIR not in sys.path:
        sys.path.insert(0, LIB_DIR)

    try:
        from lib import providers
        print("[+] Successfully loaded native providers.py")
        print("-" * 50)

        provider_data = None
        
        if hasattr(providers, 'get_providers'):
            provider_data = providers.get_providers()
        elif hasattr(providers, 'PROVIDERS'):
            provider_data = providers.PROVIDERS
        elif hasattr(providers, 'get_provider_list'):
            provider_data = providers.get_provider_list()

        # Process and save the exact raw extracted data
        if provider_data:
            # Print a quick preview to the console for your GitHub Actions logs
            print("\n[+] Extracted Provider Data Preview:")
            if isinstance(provider_data, list) and len(provider_data) > 0:
                 print(f"  First item: {provider_data[0]}")
            elif isinstance(provider_data, dict):
                 print(f"  Keys found: {list(provider_data.keys())}")
                 
            # Write the data to providors.json, overwriting it every time
            output_filename = "providors.json"
            with open(output_filename, "w", encoding="utf-8") as json_file:
                json.dump(provider_data, json_file, indent=2, ensure_ascii=False)
                
            print(f"\n[SUCCESS] Provider data updated and saved to {output_filename}")
            
        else:
            print("\n[*] Could not automatically invoke a provider getter function. No JSON created.")

    except Exception as e:
        print(f"[-] Execution Error: {e}")



if __name__ == "__main__":
    setup_environment()
    mock_kodi_modules()
    fetch_provider_names()
