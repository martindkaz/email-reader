import requests
from bs4 import BeautifulSoup
from config import GRAPH_API_ENDPOINT


class GraphClient:
    def __init__(self, auth):
        self.auth = auth
        self.endpoint = GRAPH_API_ENDPOINT

    def _make_request(self, url):
        headers = {
            'Authorization': f'Bearer {self.auth.get_access_token()}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_recent_emails(self, count=3):
        url = f"{self.endpoint}/me/messages?$top={count}&$orderby=receivedDateTime desc"
        url += "&$select=subject,from,receivedDateTime,bodyPreview"
        
        try:
            data = self._make_request(url)
            return data.get('value', [])
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching emails: {e}")
            return []

    def search_emails_by_recipient(self, recipient_email, count=3):
        search_query = f"to:{recipient_email}"
        url = f"{self.endpoint}/me/messages?$search=\"{search_query}\"&$top={count}"
        url += "&$select=subject,from,receivedDateTime,bodyPreview,toRecipients"
        
        try:
            data = self._make_request(url)
            return data.get('value', [])
        except requests.exceptions.HTTPError as e:
            print(f"Error searching emails: {e}")
            if hasattr(e.response, 'text'):
                print(f"Error details: {e.response.text}")
            return []

    def get_next_email(self, recipient_email=None, next_link=None):
        if next_link:
            url = next_link
        else:
            search_query = f"to:{recipient_email}"
            url = f"{self.endpoint}/me/messages?$search=\"{search_query}\"&$top=1"
            url += "&$select=id,subject,from,receivedDateTime,toRecipients,uniqueBody,internetMessageId,conversationId"
        
        try:
            data = self._make_request(url)
            emails = data.get('value', [])
            return emails[0] if emails else None, data.get('@odata.nextLink')
        except requests.exceptions.HTTPError as e:
            print(f"Error searching emails: {e}")
            if hasattr(e.response, 'text'):
                print(f"Error details: {e.response.text}")
            return None, None

    def clean_html_content(self, html_content):
        """Convert HTML content to clean plain text"""
        if not html_content:
            return "No content"
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text with line breaks preserved
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace while preserving paragraph breaks
        lines = [line.strip() for line in text.split('\n')]
        # Remove empty lines but keep single line breaks between paragraphs
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty and cleaned_lines:
                cleaned_lines.append('')
                prev_empty = True
        
        return '\n'.join(cleaned_lines)

    def format_email(self, email):
        received_date = email.get('receivedDateTime', 'Unknown')
        from_email = email.get('from', {}).get('emailAddress', {})
        sender_name = from_email.get('name', 'Unknown')
        sender_address = from_email.get('address', 'Unknown')
        subject = email.get('subject', 'No Subject')
        preview = email.get('bodyPreview', 'No content')
        
        return {
            'received': received_date,
            'from': f"{sender_name} <{sender_address}>",
            'subject': subject,
            'preview': preview[:200] + '...' if len(preview) > 200 else preview
        }

    def display_full_email(self, email):
        print("=" * 80)
        print("EMAIL DETAILS")
        print("=" * 80)
        
        # Headers
        from_email = email.get('from', {}).get('emailAddress', {})
        sender_name = from_email.get('name', 'Unknown')
        sender_address = from_email.get('address', 'Unknown')
        
        print(f"From: {sender_name} <{sender_address}>")
        print(f"Subject: {email.get('subject', 'No Subject')}")
        print(f"Received: {email.get('receivedDateTime', 'Unknown')}")
        
        # Recipients
        to_recipients = email.get('toRecipients', [])
        if to_recipients:
            to_list = []
            for recipient in to_recipients:
                addr = recipient.get('emailAddress', {})
                name = addr.get('name', '')
                address = addr.get('address', '')
                if name:
                    to_list.append(f"{name} <{address}>")
                else:
                    to_list.append(address)
            print(f"To: {', '.join(to_list)}")
        
        unique_body = email.get('uniqueBody', {})
        if unique_body and unique_body.get('content'):
            print("\n" + "-" * 38 + " UNIQUE BODY " + "-" * 38)
            clean_content = self.clean_html_content(unique_body.get('content', ''))
            print(clean_content)
        else:
            print("\n" + "-" * 38 + " UNIQUE BODY " + "-" * 38)
            print("No unique body content available")
        
        print("=" * 80)