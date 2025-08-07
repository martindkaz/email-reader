import requests
import os
import tempfile
import base64
from bs4 import BeautifulSoup
from config import GRAPH_API_ENDPOINT


class GraphClient:
    def __init__(self, auth):
        self.auth = auth
        self.endpoint = GRAPH_API_ENDPOINT
        self.temp_dir = None

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
            url += "&$select=id,subject,from,receivedDateTime,toRecipients,uniqueBody,internetMessageId,conversationId,hasAttachments"
        
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

    def create_temp_dir(self):
        """Create a temporary directory for attachments"""
        if self.temp_dir:
            self.cleanup_temp_dir()
        self.temp_dir = tempfile.mkdtemp(prefix="email_attachments_")
        return self.temp_dir

    def cleanup_temp_dir(self):
        """Clean up temporary directory and all files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def get_email_attachments(self, email_id):
        """Get attachments for a specific email"""
        url = f"{self.endpoint}/me/messages/{email_id}/attachments"
        try:
            data = self._make_request(url)
            return data.get('value', [])
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching attachments: {e}")
            return []

    def download_attachment(self, attachment, temp_dir):
        """Download an attachment to temporary directory"""
        try:
            # Handle file attachments
            if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                content_bytes = attachment.get('contentBytes')
                if content_bytes:
                    # Decode base64 content
                    file_content = base64.b64decode(content_bytes)
                    filename = attachment.get('name', 'unnamed_attachment')
                    
                    # Create safe filename
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
                    if not safe_filename:
                        safe_filename = 'unnamed_attachment'
                    
                    filepath = os.path.join(temp_dir, safe_filename)
                    
                    # Handle filename conflicts
                    counter = 1
                    base_filepath = filepath
                    while os.path.exists(filepath):
                        name, ext = os.path.splitext(base_filepath)
                        filepath = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_content)
                    
                    return {
                        'name': attachment.get('name', 'unnamed'),
                        'size': attachment.get('size', 0),
                        'filepath': filepath,
                        'contentType': attachment.get('contentType', 'unknown')
                    }
        except Exception as e:
            print(f"Error downloading attachment {attachment.get('name', 'unknown')}: {e}")
        
        return None

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
        
        # Handle attachments
        if email.get('hasAttachments'):
            print("\n" + "-" * 37 + " ATTACHMENTS " + "-" * 37)
            attachments = self.get_email_attachments(email.get('id'))
            
            if attachments:
                # Create temp directory for this email's attachments
                temp_dir = self.create_temp_dir()
                print(f"📎 {len(attachments)} attachment(s) found:")
                
                downloaded_attachments = []
                for i, attachment in enumerate(attachments, 1):
                    name = attachment.get('name', 'unnamed')
                    size = attachment.get('size', 0)
                    content_type = attachment.get('contentType', 'unknown')
                    
                    print(f"  {i}. {name} ({size} bytes, {content_type})")
                    
                    # Download the attachment
                    downloaded = self.download_attachment(attachment, temp_dir)
                    if downloaded:
                        downloaded_attachments.append(downloaded)
                        print(f"     ✓ Downloaded to: {downloaded['filepath']}")
                    else:
                        print(f"     ✗ Failed to download")
                
                if downloaded_attachments:
                    print(f"\n💾 All attachments saved to: {temp_dir}")
                else:
                    print("\n❌ No attachments could be downloaded")
            else:
                print("No attachments found (may be inline or reference attachments)")
        
        unique_body = email.get('uniqueBody', {})
        if unique_body and unique_body.get('content'):
            print("\n" + "-" * 38 + " UNIQUE BODY " + "-" * 38)
            clean_content = self.clean_html_content(unique_body.get('content', ''))
            print(clean_content)
        else:
            print("\n" + "-" * 38 + " UNIQUE BODY " + "-" * 38)
            print("No unique body content available")
        
        print("=" * 80)