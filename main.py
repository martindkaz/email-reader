#!/usr/bin/env python3
from auth import DeviceFlowAuth
from auth_interactive import InteractiveAuth
from graph_client import GraphClient


def main():
    print("Microsoft Graph Email Reader")
    print("=" * 40)
    
    # Try interactive auth first (with caching)
    auth = InteractiveAuth()
    print("\nAttempting authentication (cached or interactive)...")
    
    if not auth.authenticate():
        print("\nInteractive authentication failed. Trying device flow...")
        auth = DeviceFlowAuth()
        if not auth.authenticate():
            print("All authentication methods failed. Exiting.")
            return
    
    client = GraphClient(auth)
    
    print("\nSearching for emails sent to belterra-maintenance@googlegroups.com...")
    emails = client.search_emails_by_recipient("belterra-maintenance@googlegroups.com", count=3)
    
    if not emails:
        print("No emails found or unable to fetch emails.")
        return
    
    print(f"\nFound {len(emails)} emails sent to belterra-maintenance@googlegroups.com:\n")
    
    for i, email in enumerate(emails, 1):
        formatted = client.format_email(email)
        print(f"Email {i}:")
        print(f"  From: {formatted['from']}")
        print(f"  Subject: {formatted['subject']}")
        print(f"  Received: {formatted['received']}")
        print(f"  Preview: {formatted['preview']}")
        print("-" * 40)


if __name__ == "__main__":
    main()