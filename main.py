#!/usr/bin/env python3
import argparse
from auth import DeviceFlowAuth
from auth_interactive import InteractiveAuth
from graph_client import GraphClient
from parsed_email_tracker import ParsedEmailTracker


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microsoft Graph Email Reader')
    parser.add_argument('-ignr_prev', '--ignore-previous', action='store_true',
                        help='Ignore previously processed emails and re-process all emails')
    args = parser.parse_args()
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
    
    # Initialize tracker only if not ignoring previous emails
    tracker = None
    if not args.ignore_previous:
        tracker = ParsedEmailTracker()
    print("\nStarting interactive email exploration.")
    if tracker:
        print(f"Previously processed: {tracker.get_processed_count()} emails")
    else:
        print("Ignoring previously processed emails - will re-process all emails")
    print("Will process emails one by one, starting from most recent.\n")
    
    next_link = None
    search_query = "to:martin@socialcogs.net"
    email_count = 0
    skipped_count = 0

    while True:
        # Get next email (one at a time)
        emails, next_link = client.search_emails(query=search_query, page_size=1, next_link=next_link)
        email = emails[0] if emails else None
        
        if not email:
            print("No more emails found.")
            break
        
        internet_message_id = email.get('internetMessageId')
        
        # Check if already processed (only if tracker is enabled)
        if tracker and internet_message_id and tracker.is_processed(internet_message_id):
            skipped_count += 1
            print(f"⏭️  Skipping already processed email #{email_count + skipped_count}")
            continue
        
        email_count += 1
        print(f"\n📧 EMAIL #{email_count + skipped_count}")
        client.display_full_email(email)
        
        # Mark as processed (only if tracker is enabled)
        if tracker and internet_message_id:
            tracker.mark_processed(internet_message_id)
        
        # Ask user to continue
        try:
            input("\nPress Enter for next email (or Ctrl+C to exit): ")
            # Clean up attachments from current email before proceeding
            client.cleanup_temp_dir()
        except KeyboardInterrupt:
            print("\nExiting email exploration.")
            break
    
    if tracker:
        print(f"\nCompleted exploration. Processed {email_count} new emails, skipped {skipped_count} already processed.")
    else:
        print(f"\nCompleted exploration. Processed {email_count} emails (ignoring previous processing status).")
    
    # Final cleanup
    client.cleanup_temp_dir()


if __name__ == "__main__":
    main()
