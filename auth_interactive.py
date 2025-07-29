import msal
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
        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY
        )
        self.access_token = None
    
    def authenticate(self):
        # First try to get token from cache
        accounts = self.app.get_accounts()
        if accounts:
            print("Found cached account, attempting silent authentication...")
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                print("Authentication successful (from cache)!")
                return True
        
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
            return True
        else:
            print(f"\nAuthentication failed: {result.get('error')}")
            print(f"Error description: {result.get('error_description')}")
            return False
    
    def get_access_token(self):
        if not self.access_token:
            self.authenticate()
        return self.access_token