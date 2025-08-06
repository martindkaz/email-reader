import msal
import os
from config import CLIENT_ID, AUTHORITY, SCOPES


# Interactive Authentication using MSAL Python
# 
# IMPORTANT: This uses MSAL Python's default interactive flow which:
# - Opens the system's default web browser for authentication
# - Runs a local web server on http://localhost:<random_port> to catch the redirect
# - Does NOT use the native client redirect URI (https://login.microsoftonline.com/common/oauth2/nativeclient)
#
# TODO: To make this work, you need to add "http://localhost" as a redirect URI in your 
# Azure app registration under Authentication > Platform configurations > Mobile and desktop applications
#
# Note: MSAL Python doesn't support the native client redirect URI that other MSAL libraries use.
# If you need that specific flow, you would need to use MSAL.NET or implement OAuth manually.

class InteractiveAuth:
    def __init__(self):
        # Create a persistent token cache file
        cache = msal.SerializableTokenCache()
        cache_file = "token_cache.bin"
        
        # Load existing cache if it exists
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache.deserialize(f.read())
        
        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=cache
        )
        self.access_token = None
        self.cache_file = cache_file
    
    def authenticate(self):
        # First try to get token from cache
        accounts = self.app.get_accounts()
        if accounts:
            print("Found cached account, attempting silent authentication...")
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                print("Authentication successful (from cache)!")
                self._save_cache()
                return True
            else:
                print("Cached token expired or invalid, need interactive authentication...")
        
        # If no cached token, do interactive authentication
        print("\nStarting interactive authentication...")
        print("A browser window will open for you to sign in.")
        
        result = self.app.acquire_token_interactive(
            scopes=SCOPES,
            prompt="select_account"
        )
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            print("\nAuthentication successful!")
            self._save_cache()
            return True
        else:
            print(f"\nAuthentication failed: {result.get('error')}")
            print(f"Error description: {result.get('error_description')}")
            return False
    
    def _save_cache(self):
        """Save the token cache to file"""
        if self.app.token_cache.has_state_changed:
            with open(self.cache_file, 'w') as f:
                f.write(self.app.token_cache.serialize())
    
    def get_access_token(self):
        if not self.access_token:
            if not self.authenticate():
                return None
        
        # Try to refresh token if needed
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                self._save_cache()
            elif "error" in result:
                # Token expired, re-authenticate
                print("Token expired, re-authenticating...")
                if not self.authenticate():
                    return None
        
        return self.access_token