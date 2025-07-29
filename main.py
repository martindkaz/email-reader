#!/usr/bin/env python3
from auth import DeviceFlowAuth
from auth_interactive import InteractiveAuth
from graph_client import GraphClient


def main():
    print("Microsoft Graph Email Reader")
    print("=" * 40)
    
    print("\nSelect authentication method:")
    print("1. Device Flow (enter code on another device)")
    print("2. Interactive (browser-based login)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        auth = DeviceFlowAuth()
    elif choice == "2":
        auth = InteractiveAuth()
    else:
        print("Invalid choice. Exiting.")
        return
    
    if not auth.authenticate():
        print("Authentication failed. Exiting.")
        return
    
    client = GraphClient(auth)
    
    print("\nFetching recent emails...")
    emails = client.get_recent_emails(count=5)
    
    if not emails:
        print("No emails found or unable to fetch emails.")
        return
    
    print(f"\nFound {len(emails)} recent emails:\n")
    
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