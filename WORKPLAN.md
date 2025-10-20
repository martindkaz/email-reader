
- separate clargs/funcs for AND and OR with words



- Rename display_full_email() to process_email()

- belterra-maintenance@googlegroups.com

- Seed well NER & context
- Do NER with each email, check with user for confirmations
- It's going to be useful to go back after some initial discovery and redo the NER name entity recognition process and enriching

- save extracted email as formatted by display_full_email() in Neo4J DB as a new node. We'll create edges later. Save the email's internetMessageId as a node property in a way that allows us to create an index over it for faster search later. 

# DONE / To DOC
- Starts parsing from the oldest emails in order to capture the initial context where the name of the use case etc might be.

# ✅ COMPLETED - 2025-10-19
## LangGraph Agent with Claude Sonnet 4.5
**Branch**: feature/langgraph-agent

### What Was Built
- MCP server exposing email search tools (search_emails, get_email_details, list_email_attachments)
- LangGraph agent with Claude Sonnet 4.5 for natural language email queries
- Interactive and single-query CLI modes (run_agent.py)
- Reuses existing MSAL auth and Graph API client
- Comprehensive documentation in README.md and dev_docs/

### Files Created
- mcp_server/ - MCP server implementation
- langgraph_agent/ - LangGraph agent with Claude integration
- run_agent.py - Main entry point
- setup_agent.sh - Automated setup
- requirements-agent.txt - Dependencies
- .env.example - Environment variable template
- Documentation: README.md, dev_docs/langgraph_agent_architecture.md, IMPLEMENTATION_SUMMARY.md

### Next Steps for User
1. Add ANTHROPIC_API_KEY to .env file
2. Run ./setup_agent.sh to install dependencies
3. Test: python run_agent.py
4. Try queries like "Find emails about project updates"

### Dependencies Added to requirements-agent.txt
- mcp >= 1.0.0
- langgraph >= 0.2.0
- langchain-anthropic >= 0.1.0
- anthropic >= 0.39.0
- langchain-core >= 0.3.0
- pydantic >= 2.0.0

