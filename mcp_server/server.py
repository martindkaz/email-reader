"""
MCP Server for Outlook Email Search

This server exposes Microsoft Graph email operations as MCP tools.
Uses MSAL for authentication with interactive browser flow on first run.
"""

import json
import logging
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our existing auth and graph client
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_interactive import InteractiveAuth
from graph_client import GraphClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailMCPServer:
    """MCP Server for email operations"""

    def __init__(self):
        self.server = Server("email-search-server")
        self.auth = None
        self.graph_client = None
        self._setup_handlers()

    def _ensure_authenticated(self):
        """Ensure authentication is complete before operations"""
        if self.auth is None:
            logger.info("Initializing authentication...")
            self.auth = InteractiveAuth()
            # This will trigger browser auth on first run if no cached token
            token = self.auth.get_access_token()
            if not token:
                raise RuntimeError("Authentication failed")
            logger.info("Authentication successful")

        if self.graph_client is None:
            self.graph_client = GraphClient(self.auth)

    def _setup_handlers(self):
        """Set up MCP tool handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available email tools"""
            return [
                Tool(
                    name="search_emails",
                    description=(
                        "Search emails in Outlook mailbox using Microsoft Graph API. "
                        "Supports various match modes: 'raw' (default), 'single' (exact phrase), "
                        "'and' (all words must match), 'or' (any word matches), 'phrase' (exact phrase in quotes). "
                        "Returns a formatted text block with email details including sender, subject, date, recipients, and body content."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string (e.g., 'meeting notes', 'project update')"
                            },
                            "page_size": {
                                "type": "number",
                                "description": "Number of emails to return (default: 50, max: 100)",
                                "default": 50
                            },
                            "match_mode": {
                                "type": "string",
                                "enum": ["raw", "single", "and", "or", "phrase"],
                                "description": "Search mode: 'raw' (default query), 'single' (exact match), 'and' (all words), 'or' (any word), 'phrase' (exact phrase)",
                                "default": "raw"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_email_details",
                    description=(
                        "Get full details of a specific email by its ID. "
                        "Returns complete email information including headers, body, and attachment metadata. "
                        "Use this after searching to get the full content of a specific email."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "The Graph API email ID (from search results)"
                            }
                        },
                        "required": ["email_id"]
                    }
                ),
                Tool(
                    name="list_email_attachments",
                    description=(
                        "List attachments for a specific email. "
                        "Returns attachment names, sizes, and content types. "
                        "Does not download attachments, only lists metadata."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "The Graph API email ID"
                            }
                        },
                        "required": ["email_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls"""
            try:
                # Ensure authentication before any operation
                self._ensure_authenticated()

                if name == "search_emails":
                    return await self._search_emails(arguments)
                elif name == "get_email_details":
                    return await self._get_email_details(arguments)
                elif name == "list_email_attachments":
                    return await self._list_attachments(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    async def _search_emails(self, args: dict) -> list[TextContent]:
        """Search emails and return formatted text"""
        query = args.get("query")
        page_size = args.get("page_size", 50)
        match_mode = args.get("match_mode", "raw")

        if not query:
            return [TextContent(
                type="text",
                text="Error: query parameter is required"
            )]

        logger.info(f"Searching emails with query: {query}, mode: {match_mode}, page_size: {page_size}")

        # Use the existing graph client method
        result_text = self.graph_client.search_and_combine_emails(
            query=query,
            page_size=min(page_size, 100),  # Cap at 100
            match_mode=match_mode
        )

        if not result_text or result_text.strip() == "":
            result_text = f"No emails found matching query: {query}"

        return [TextContent(
            type="text",
            text=result_text
        )]

    async def _get_email_details(self, args: dict) -> list[TextContent]:
        """Get details of a specific email"""
        email_id = args.get("email_id")

        if not email_id:
            return [TextContent(
                type="text",
                text="Error: email_id parameter is required"
            )]

        logger.info(f"Getting email details for: {email_id}")

        try:
            # Fetch the email using Graph API
            url = f"{self.graph_client.endpoint}/me/messages/{email_id}"
            headers = {
                'Authorization': f'Bearer {self.auth.get_access_token()}',
                'Content-Type': 'application/json'
            }

            import requests
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            email = response.json()

            # Format email details
            formatted = self._format_email_details(email)

            return [TextContent(
                type="text",
                text=formatted
            )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching email details: {str(e)}"
            )]

    async def _list_attachments(self, args: dict) -> list[TextContent]:
        """List attachments for an email"""
        email_id = args.get("email_id")

        if not email_id:
            return [TextContent(
                type="text",
                text="Error: email_id parameter is required"
            )]

        logger.info(f"Listing attachments for email: {email_id}")

        attachments = self.graph_client.get_email_attachments(email_id)

        if not attachments:
            return [TextContent(
                type="text",
                text="No attachments found for this email"
            )]

        # Format attachment list
        lines = [f"Found {len(attachments)} attachment(s):\n"]
        for i, att in enumerate(attachments, 1):
            name = att.get('name', 'unnamed')
            size = att.get('size', 0)
            content_type = att.get('contentType', 'unknown')
            lines.append(f"{i}. {name} ({size} bytes, {content_type})")

        return [TextContent(
            type="text",
            text="\n".join(lines)
        )]

    def _format_email_details(self, email: dict) -> str:
        """Format email details as text"""
        lines = ["=" * 80, "EMAIL DETAILS", "=" * 80]

        # From
        from_email = email.get('from', {}).get('emailAddress', {})
        sender_name = from_email.get('name', 'Unknown')
        sender_address = from_email.get('address', 'Unknown')
        lines.append(f"From: {sender_name} <{sender_address}>")

        # Subject
        lines.append(f"Subject: {email.get('subject', 'No Subject')}")

        # Date
        lines.append(f"Received: {email.get('receivedDateTime', 'Unknown')}")

        # To Recipients
        to_recipients = email.get('toRecipients', [])
        if to_recipients:
            to_list = []
            for recipient in to_recipients:
                addr = recipient.get('emailAddress', {})
                name = addr.get('name', '')
                address = addr.get('address', '')
                to_list.append(f"{name} <{address}>" if name else address)
            lines.append(f"To: {', '.join(to_list)}")

        # Attachments
        if email.get('hasAttachments'):
            lines.append(f"\nHas Attachments: Yes")

        # Body
        body = email.get('body', {})
        if body and body.get('content'):
            lines.append("\n" + "-" * 40 + " BODY " + "-" * 40)
            clean_content = self.graph_client.clean_html_content(body.get('content', ''))
            lines.append(clean_content)

        lines.append("=" * 80)
        return "\n".join(lines)

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Email MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = EmailMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
