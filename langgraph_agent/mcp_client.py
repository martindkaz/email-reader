"""
MCP Client for connecting to the Email Search MCP Server

This client wraps the MCP protocol and provides simple Python methods
for the LangGraph agent to use.
"""

import json
import logging
import subprocess
import sys
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPEmailClient:
    """Client for communicating with the Email MCP Server"""

    def __init__(self):
        self.process = None
        self.session = None

    def connect(self):
        """
        Connect to the MCP server

        Note: For simplicity, we're directly importing the server modules
        instead of running as a subprocess. In production, you might want
        to run the MCP server as a separate process.
        """
        logger.info("Connecting to MCP server...")

        # Import the server components
        try:
            # Add parent directory to path
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            from mcp_server.server import EmailMCPServer
            self.server = EmailMCPServer()
            self.server._ensure_authenticated()  # Authenticate on connect
            logger.info("Connected to MCP server")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    def disconnect(self):
        """Disconnect from the MCP server"""
        if self.server:
            # Clean up any resources if needed
            if hasattr(self.server, 'graph_client') and self.server.graph_client:
                self.server.graph_client.cleanup_temp_dir()
            logger.info("Disconnected from MCP server")

    def search_emails(
        self,
        query: str,
        page_size: int = 50,
        match_mode: str = "raw"
    ) -> str:
        """
        Search emails using the MCP server

        Args:
            query: Search query string
            page_size: Number of results to return
            match_mode: Search mode (raw, single, and, or, phrase)

        Returns:
            Formatted text with search results
        """
        if not self.server:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        import asyncio

        args = {
            "query": query,
            "page_size": page_size,
            "match_mode": match_mode
        }

        # Run the async method synchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(self.server._search_emails(args))

        # Extract text from TextContent
        if result and len(result) > 0:
            return result[0].text
        return "No results"

    def get_email_details(self, email_id: str) -> str:
        """
        Get details of a specific email

        Args:
            email_id: The email ID from Graph API

        Returns:
            Formatted email details
        """
        if not self.server:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        import asyncio

        args = {"email_id": email_id}

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(self.server._get_email_details(args))

        if result and len(result) > 0:
            return result[0].text
        return "No details available"

    def list_attachments(self, email_id: str) -> str:
        """
        List attachments for an email

        Args:
            email_id: The email ID from Graph API

        Returns:
            List of attachments
        """
        if not self.server:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        import asyncio

        args = {"email_id": email_id}

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(self.server._list_attachments(args))

        if result and len(result) > 0:
            return result[0].text
        return "No attachments"
