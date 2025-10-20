"""
LangGraph Agent with Claude Sonnet 4.5 and MCP Tools

This agent can search and analyze Outlook emails using the MCP server.
"""

import logging
from typing import Annotated, TypedDict, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, AGENT_VERBOSE
from .mcp_client import MCPEmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State of the agent conversation"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


class EmailSearchAgent:
    """LangGraph agent for email search operations"""

    def __init__(self):
        self.mcp_client = MCPEmailClient()
        self.llm = ChatAnthropic(
            model=CLAUDE_MODEL,
            api_key=ANTHROPIC_API_KEY,
            temperature=0.7
        )
        self.graph = None
        self._setup_tools()
        self._build_graph()

    def _setup_tools(self):
        """Set up LangChain tools that wrap MCP operations"""

        @tool
        def search_emails(
            query: str,
            page_size: int = 50,
            match_mode: str = "raw"
        ) -> str:
            """
            Search emails in Outlook mailbox.

            Args:
                query: Search query string (e.g., 'meeting notes', 'project update')
                page_size: Number of emails to return (default: 50, max: 100)
                match_mode: Search mode - 'raw' (default), 'single', 'and', 'or', 'phrase'

            Returns:
                Formatted text with email details
            """
            logger.info(f"Tool called: search_emails(query={query}, page_size={page_size}, match_mode={match_mode})")
            return self.mcp_client.search_emails(query, page_size, match_mode)

        @tool
        def get_email_details(email_id: str) -> str:
            """
            Get full details of a specific email.

            Args:
                email_id: The Graph API email ID from search results

            Returns:
                Complete email information including headers, body, and attachments
            """
            logger.info(f"Tool called: get_email_details(email_id={email_id})")
            return self.mcp_client.get_email_details(email_id)

        @tool
        def list_email_attachments(email_id: str) -> str:
            """
            List attachments for a specific email.

            Args:
                email_id: The Graph API email ID

            Returns:
                List of attachment names, sizes, and content types
            """
            logger.info(f"Tool called: list_email_attachments(email_id={email_id})")
            return self.mcp_client.list_attachments(email_id)

        self.tools = [search_emails, get_email_details, list_email_attachments]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _build_graph(self):
        """Build the LangGraph workflow"""

        def should_continue(state: AgentState):
            """Determine if we should continue or end"""
            messages = state["messages"]
            last_message = messages[-1]

            # If there are no tool calls, we're done
            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return END

            return "tools"

        def call_model(state: AgentState):
            """Call the LLM with current state"""
            messages = state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(self.tools))

        # Set entry point
        workflow.set_entry_point("agent")

        # Add edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )

        # After tools, go back to agent
        workflow.add_edge("tools", "agent")

        # Compile the graph
        self.graph = workflow.compile()

    def run(self, user_query: str) -> str:
        """
        Run the agent with a user query

        Args:
            user_query: The user's question or request

        Returns:
            The agent's response
        """
        logger.info(f"Running agent with query: {user_query}")

        # Initialize the MCP client connection
        self.mcp_client.connect()

        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_query)]
            }

            # Run the graph
            final_state = self.graph.invoke(initial_state)

            # Extract the final response
            messages = final_state["messages"]
            last_message = messages[-1]

            if isinstance(last_message, AIMessage):
                return last_message.content
            else:
                return str(last_message)

        finally:
            # Clean up MCP connection
            self.mcp_client.disconnect()

    async def arun(self, user_query: str) -> str:
        """
        Async version of run

        Args:
            user_query: The user's question or request

        Returns:
            The agent's response
        """
        logger.info(f"Running agent (async) with query: {user_query}")

        # Initialize the MCP client connection
        self.mcp_client.connect()

        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_query)]
            }

            # Run the graph asynchronously
            final_state = await self.graph.ainvoke(initial_state)

            # Extract the final response
            messages = final_state["messages"]
            last_message = messages[-1]

            if isinstance(last_message, AIMessage):
                return last_message.content
            else:
                return str(last_message)

        finally:
            # Clean up MCP connection
            self.mcp_client.disconnect()

    def stream(self, user_query: str):
        """
        Stream the agent's execution

        Args:
            user_query: The user's question or request

        Yields:
            State updates as the agent executes
        """
        logger.info(f"Streaming agent with query: {user_query}")

        # Initialize the MCP client connection
        self.mcp_client.connect()

        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_query)]
            }

            # Stream the graph execution
            for state in self.graph.stream(initial_state):
                yield state

        finally:
            # Clean up MCP connection
            self.mcp_client.disconnect()
