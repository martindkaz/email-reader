import requests
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