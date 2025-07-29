import msal
from config import CLIENT_ID, AUTHORITY, SCOPES


class DeviceFlowAuth:
    def __init__(self):
        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY
        )
        self.access_token = None

    def authenticate(self):
        flow = self.app.initiate_device_flow(scopes=SCOPES)
        
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow. Ensure Azure App is set up as a Public Client.")
        
        print(f"To sign in, visit {flow['verification_uri']}")
        print(f"Enter the code: {flow['user_code']}")
        print("\nWaiting for authentication...")
        
        result = self.app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            print("Authentication successful!")
            return True
        else:
            print(f"Authentication failed: {result.get('error')}")
            print(f"Error description: {result.get('error_description')}")
            return False

    def get_access_token(self):
        if not self.access_token:
            self.authenticate()
        return self.access_token