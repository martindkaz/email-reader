#!/usr/bin/env python3
from auth import DeviceFlowAuth
from auth_interactive import InteractiveAuth
from graph_client import GraphClient
from parsed_email_tracker import ParsedEmailTracker


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
    tracker = ParsedEmailTracker()
    
    print("\nStarting interactive email exploration for belterra-maintenance@googlegroups.com...")
    print(f"Previously processed: {tracker.get_processed_count()} emails")
    print("Will process emails one by one, starting from most recent.\n")
    
    next_link = None
    email_count = 0
    skipped_count = 0
    
    while True:
        # Get next email
        email, next_link = client.get_next_email("belterra-maintenance@googlegroups.com", next_link)
        
        if not email:
            print("No more emails found.")
            break
        
        internet_message_id = email.get('internetMessageId')
        
        # Check if already processed
        if internet_message_id and tracker.is_processed(internet_message_id):
            skipped_count += 1
            print(f"⏭️  Skipping already processed email #{email_count + skipped_count}")
            continue
        
        email_count += 1
        print(f"\n📧 EMAIL #{email_count + skipped_count}")
        client.display_full_email(email)
        
        # Mark as processed
        if internet_message_id:
            tracker.mark_processed(internet_message_id)
        
        # Ask user to continue
        try:
            continue_choice = input("\nContinue to next email? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("Exiting email exploration.")
                break
            else:
                # Clean up attachments from current email before proceeding
                client.cleanup_temp_dir()
        except KeyboardInterrupt:
            print("\nExiting email exploration.")
            break
    
    print(f"\nCompleted exploration. Processed {email_count} new emails, skipped {skipped_count} already processed.")
    
    # Final cleanup
    client.cleanup_temp_dir()


if __name__ == "__main__":
    main()