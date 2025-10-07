#!/usr/bin/env python3
import argparse
from typing import List

from auth import DeviceFlowAuth
from auth_interactive import InteractiveAuth
from graph_client import GraphClient
from parsed_email_tracker import ParsedEmailTracker


DEFAULT_SEARCH_QUERY = "to:martin@socialcogs.net"


def authenticate_and_prepare(ignore_previous: bool):
    """Authenticate the user and prepare shared client/tracker state."""
    print("Microsoft Graph Email Reader")
    print("=" * 40)

    auth = InteractiveAuth()
    print("\nAttempting authentication (cached or interactive)...")

    if not auth.authenticate():
        print("\nInteractive authentication failed. Trying device flow...")
        auth = DeviceFlowAuth()
        if not auth.authenticate():
            print("All authentication methods failed. Exiting.")
            return None, None

    client = GraphClient(auth)
    tracker = None if ignore_previous else ParsedEmailTracker()
    return client, tracker


def run_one_by_one(
    client: GraphClient,
    tracker: ParsedEmailTracker,
    search_query: str,
    match_mode: str,
) -> None:
    """Interactive mode: walk emails one at a time."""
    print("\nStarting interactive email exploration.")
    if tracker:
        print(f"Previously processed: {tracker.get_processed_count()} emails")
    else:
        print("Ignoring previously processed emails - will re-process all emails")
    print("Will process emails one by one, starting from most recent.\n")

    next_link = None
    email_count = 0
    skipped_count = 0

    while True:
        emails, next_link = client.search_emails(
            query=search_query,
            page_size=1,
            next_link=next_link,
            match_mode=match_mode,
        )
        email = emails[0] if emails else None

        if not email:
            print("No more emails found.")
            break

        internet_message_id = email.get('internetMessageId')

        if tracker and internet_message_id and tracker.is_processed(internet_message_id):
            skipped_count += 1
            print(f"⏭️  Skipping already processed email #{email_count + skipped_count}")
            continue

        email_count += 1
        print(f"\n📧 EMAIL #{email_count + skipped_count}")
        client.display_full_email(email)

        if tracker and internet_message_id:
            tracker.mark_processed(internet_message_id)

        try:
            input("\nPress Enter for next email (or Ctrl+C to exit): ")
            client.cleanup_temp_dir()
        except KeyboardInterrupt:
            print("\nExiting email exploration.")
            break

    if tracker:
        print(f"\nCompleted exploration. Processed {email_count} new emails, skipped {skipped_count} already processed.")
    else:
        print(f"\nCompleted exploration. Processed {email_count} emails (ignoring previous processing status).")

    client.cleanup_temp_dir()


def run_search_combine(
    client: GraphClient,
    tracker: ParsedEmailTracker,
    search_query: str,
    page_size: int,
    match_mode: str,
) -> None:
    """Batch mode: fetch a set of emails and print a combined summary."""
    print("\nGenerating combined email summary...")

    emails, _ = client.search_emails(
        query=search_query,
        page_size=page_size,
        match_mode=match_mode,
    )
    if not emails:
        print("No emails found for the provided query.")
        return

    filtered_emails: List[dict] = []
    skipped = 0
    if tracker:
        for email in emails:
            message_id = email.get('internetMessageId')
            if message_id and tracker.is_processed(message_id):
                skipped += 1
                continue
            filtered_emails.append(email)
    else:
        filtered_emails = emails

    if not filtered_emails:
        print("No new emails to include in the combined output.")
        return

    combined_text = client.format_email_batch(filtered_emails)
    print(combined_text)

    if tracker:
        for email in filtered_emails:
            message_id = email.get('internetMessageId')
            if message_id:
                tracker.mark_processed(message_id)
        print(f"\nCombined output included {len(filtered_emails)} emails (skipped {skipped} already processed).")
    else:
        print(f"\nCombined output included {len(filtered_emails)} emails.")


def main():
    parser = argparse.ArgumentParser(description='Microsoft Graph Email Reader')
    parser.add_argument('-obo', '--one-by-one', action='store_true',
                        help='Interactive mode that walks emails one at a time')
    parser.add_argument('-sc', '--search-combine', action='store_true',
                        help='Run the search-and-combine summary output')
    parser.add_argument('-ip', '--ignore-previous', '--ignr_prev', dest='ignore_previous', action='store_true',
                        help='Ignore previously processed emails and re-process all emails')
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument('-q', '--query',
                             help='Raw Graph $search string (default uses AND semantics).')
    query_group.add_argument('-qAND', '--query-and', dest='query_and',
                             help='Search requiring all words (single-quoted tokens joined with AND).')
    query_group.add_argument('-qOR', '--query-or', dest='query_or',
                             help='Search matching any word (single-quoted tokens joined with OR).')
    query_group.add_argument('-qPHR', '--query-phrase', dest='query_phrase',
                             help='Search for an exact phrase (wrapped in escaped double quotes).')
    query_group.add_argument('-qDEF', '--query-single', dest='query_single',
                             help='Search using default stemming but quoting the full input once.')
    parser.add_argument('--page-size', type=int, default=50,
                        help='Page size for search-combine output (default: 50)')

    args = parser.parse_args()

    client, tracker = authenticate_and_prepare(args.ignore_previous)
    if client is None:
        return

    match_mode = 'raw'
    search_query = DEFAULT_SEARCH_QUERY
    if args.query is not None:
        search_query = args.query
        match_mode = 'raw'
    elif args.query_and is not None:
        search_query = args.query_and
        match_mode = 'and'
    elif args.query_or is not None:
        search_query = args.query_or
        match_mode = 'or'
    elif args.query_phrase is not None:
        search_query = args.query_phrase
        match_mode = 'phrase'
    elif args.query_single is not None:
        search_query = args.query_single
        match_mode = 'single'

    modes = []
    if args.one_by_one:
        modes.append('one_by_one')
    if args.search_combine:
        modes.append('search_combine')
    if not modes:
        modes.append('one_by_one')

    for mode in modes:
        if mode == 'one_by_one':
            run_one_by_one(client, tracker, search_query, match_mode)
        elif mode == 'search_combine':
            run_search_combine(client, tracker, search_query, args.page_size, match_mode)


if __name__ == "__main__":
    main()
