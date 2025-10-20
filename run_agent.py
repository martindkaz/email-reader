#!/usr/bin/env python3
"""
Email Search Agent - Interactive CLI

Run a LangGraph agent powered by Claude Sonnet 4.5 that can search
and analyze Outlook emails via MCP tools.
"""

import sys
import logging
from langgraph_agent.agent import EmailSearchAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 80)
    print("Email Search Agent - Powered by Claude Sonnet 4.5")
    print("=" * 80)
    print("\nThis agent can help you search and analyze your Outlook emails.")
    print("It uses Microsoft Graph API via an MCP server.\n")
    print("Examples:")
    print("  - 'Find emails about project updates from last week'")
    print("  - 'Search for emails with attachments about the budget'")
    print("  - 'Show me emails from john@example.com about meetings'")
    print("\nType 'quit' or 'exit' to quit.\n")
    print("=" * 80 + "\n")


def run_interactive():
    """Run the agent in interactive mode"""
    print_banner()

    # Initialize the agent
    try:
        logger.info("Initializing agent...")
        agent = EmailSearchAgent()
        logger.info("Agent initialized successfully")
    except Exception as e:
        print(f"\n❌ Error initializing agent: {e}")
        print("\nPlease ensure:")
        print("  1. ANTHROPIC_API_KEY is set in your .env file")
        print("  2. Azure AD credentials (CLIENT_ID, TENANT_ID) are configured")
        print("  3. All dependencies are installed: pip install -r requirements-agent.txt\n")
        sys.exit(1)

    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("\n🤖 You: ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            # Run the agent
            print("\n🔍 Agent: Processing your request...\n")

            try:
                response = agent.run(user_input)
                print(f"✅ Agent: {response}\n")

            except Exception as e:
                logger.error(f"Error running agent: {e}", exc_info=True)
                print(f"\n❌ Error: {str(e)}\n")
                print("Please try rephrasing your request or check the logs for details.\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break


def run_single_query(query: str):
    """Run a single query and exit"""
    try:
        logger.info(f"Running single query: {query}")
        agent = EmailSearchAgent()
        response = agent.run(query)
        print(f"\n{response}\n")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}\n")
        return 1


def main():
    """Main entry point"""
    # Check if a query was provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        sys.exit(run_single_query(query))
    else:
        run_interactive()


if __name__ == "__main__":
    main()
