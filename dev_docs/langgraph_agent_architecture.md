# LangGraph Agent Architecture

## Overview

This document describes the architecture of the LangGraph-based email search agent that uses Claude Sonnet 4.5 and Model Context Protocol (MCP) for searching Outlook emails.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (run_agent.py - CLI)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Natural Language Query
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Agent                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Claude Sonnet 4.5 (via Anthropic API)    │     │
│  │  - Understands user intent                         │     │
│  │  - Plans tool usage                                │     │
│  │  - Formats responses                               │     │
│  └────────────────┬───────────────────────────────────┘     │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐     │
│  │              LangGraph Workflow                    │     │
│  │  - Agent Node: Calls Claude with tools             │     │
│  │  - Tool Node: Executes tool calls                  │     │
│  │  - Conditional routing                             │     │
│  └────────────────┬───────────────────────────────────┘     │
└───────────────────┼──────────────────────────────────────────┘
                    │ Tool Calls (search_emails, etc.)
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client                              │
│  (langgraph_agent/mcp_client.py)                            │
│  - Wraps MCP server calls                                   │
│  - Handles async/sync conversion                            │
│  - Manages connection lifecycle                             │
└───────────────────┬─────────────────────────────────────────┘
                    │ MCP Protocol (Local)
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                              │
│  (mcp_server/server.py)                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Tools:                                            │     │
│  │  - search_emails                                   │     │
│  │  - get_email_details                               │     │
│  │  - list_email_attachments                          │     │
│  └────────────────┬───────────────────────────────────┘     │
└───────────────────┼──────────────────────────────────────────┘
                    │ Microsoft Graph API Calls
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    Graph Client                              │
│  (graph_client.py)                                          │
│  - Email search with match modes                            │
│  - Email detail fetching                                    │
│  - Attachment handling                                      │
│  - HTML content cleaning                                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                 Authentication Layer                         │
│  (auth_interactive.py)                                      │
│  - MSAL interactive browser flow                            │
│  - Token caching (token_cache.bin)                          │
│  - Silent token refresh                                     │
└───────────────────┬─────────────────────────────────────────┘
                    │ OAuth 2.0 / MSAL
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Microsoft Graph API                             │
│  (graph.microsoft.com/v1.0)                                 │
│  - Mail.Read scope                                          │
│  - /me/messages endpoint                                    │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface (run_agent.py)

**Purpose**: Entry point for running the agent

**Modes**:
- **Interactive Mode**: Continuous conversation loop
- **Single Query Mode**: One-shot query with command-line argument

**Responsibilities**:
- Parse command-line arguments
- Initialize the agent
- Handle user input/output
- Error handling and user-friendly messages

**Key Functions**:
- `run_interactive()`: Interactive CLI loop
- `run_single_query(query)`: Execute one query and exit
- `print_banner()`: Display welcome message

### 2. LangGraph Agent (langgraph_agent/agent.py)

**Purpose**: Orchestrate email searches using Claude Sonnet 4.5

**Core Components**:

#### a. Agent State
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
```
- Maintains conversation history
- Uses LangGraph's message annotation for state updates

#### b. Tools
Three LangChain tools that wrap MCP operations:

1. **search_emails**:
   - Parameters: query (str), page_size (int), match_mode (str)
   - Returns: Formatted email search results

2. **get_email_details**:
   - Parameters: email_id (str)
   - Returns: Full email content

3. **list_email_attachments**:
   - Parameters: email_id (str)
   - Returns: Attachment metadata

#### c. LangGraph Workflow

**Nodes**:
- `agent`: Calls Claude with bound tools
- `tools`: Executes tool calls via ToolNode

**Edges**:
- Conditional: From agent → tools or END (based on tool calls)
- Direct: From tools → agent (loop back for more reasoning)

**Execution Flow**:
1. User message enters as HumanMessage
2. Agent node calls Claude with tools
3. If Claude makes tool calls → route to tools node
4. Tools execute and return results
5. Loop back to agent with tool results
6. Agent processes results and responds
7. If no more tool calls → END

#### d. Claude Integration
- Model: `claude-sonnet-4-20250514` (Sonnet 4.5)
- API: Anthropic API via langchain-anthropic
- Temperature: 0.7 (balanced creativity/accuracy)

**Methods**:
- `run(query)`: Synchronous execution
- `arun(query)`: Async execution
- `stream(query)`: Streaming execution with state updates

### 3. MCP Client (langgraph_agent/mcp_client.py)

**Purpose**: Bridge between LangChain tools and MCP server

**Design Pattern**: Adapter/Wrapper

**Key Features**:
- Connection management (connect/disconnect)
- Async-to-sync conversion for synchronous tool calls
- Direct server instantiation (in-process)

**Methods**:
- `connect()`: Initialize MCP server and authenticate
- `disconnect()`: Clean up resources
- `search_emails()`: Wrapper for search tool
- `get_email_details()`: Wrapper for details tool
- `list_attachments()`: Wrapper for attachments tool

**Implementation Note**: Currently uses in-process server instantiation. Could be extended to use subprocess/network communication for true client-server separation.

### 4. MCP Server (mcp_server/server.py)

**Purpose**: Expose email operations as MCP tools

**Protocol**: Model Context Protocol (stdio-based)

**Tool Definitions**:

Each tool includes:
- Name (identifier)
- Description (for Claude to understand purpose)
- Input Schema (JSON Schema for parameters)

**Authentication Flow**:
1. `_ensure_authenticated()` called on first tool use
2. Creates `InteractiveAuth` instance
3. Gets access token (triggers browser auth if needed)
4. Creates `GraphClient` with authenticated session
5. Subsequent calls reuse cached token

**Handler Methods**:
- `list_tools()`: Returns available tools
- `call_tool()`: Routes to specific tool handler
- `_search_emails()`: Search implementation
- `_get_email_details()`: Email details implementation
- `_list_attachments()`: Attachments list implementation

**Return Format**: `list[TextContent]` - MCP protocol text responses

### 5. Graph Client (graph_client.py)

**Purpose**: Microsoft Graph API operations

**Existing Component** (reused from original CLI)

**Key Features**:
- `$search` query building with multiple match modes
- Pagination support
- HTML content cleaning (BeautifulSoup)
- Attachment handling
- Email formatting

**Search Match Modes**:
- `raw`: Pass-through query
- `single`: Exact phrase
- `and`: All words must match
- `or`: Any word matches
- `phrase`: Exact phrase in quotes

### 6. Authentication (auth_interactive.py)

**Purpose**: Azure AD authentication via MSAL

**Existing Component** (reused from original CLI)

**Flow**:
1. Check for cached token (`token_cache.bin`)
2. If cache exists → silent token acquisition
3. If cache missing/expired → interactive browser flow
4. Cache new token for future use

**MSAL Configuration**:
- Authority: `https://login.microsoftonline.com/{TENANT_ID}`
- Scopes: `['https://graph.microsoft.com/Mail.Read']`
- Redirect URI: `http://localhost` (random port)

## Data Flow Examples

### Example 1: Simple Email Search

```
User: "Find emails about project updates"
  ↓
Agent receives HumanMessage
  ↓
Claude analyzes intent → decides to use search_emails tool
  ↓
Tool call: search_emails(query="project updates", page_size=50, match_mode="raw")
  ↓
MCP Client → MCP Server → Graph Client
  ↓
Graph API: GET /me/messages?$search="project updates"
  ↓
Results flow back through stack
  ↓
Claude receives formatted email text
  ↓
Claude generates natural language response
  ↓
User sees: "I found 12 emails about project updates. Here are the most recent..."
```

### Example 2: Multi-Step Search

```
User: "Find emails from john@example.com about meetings and show me the first one"
  ↓
Agent: search_emails(query="from:john@example.com meetings")
  ↓
Results returned
  ↓
Agent: Identifies first email ID
  ↓
Agent: get_email_details(email_id="AAMkAD...")
  ↓
Full email content returned
  ↓
Agent: Formats and presents complete email details
```

## Configuration

### Environment Variables (.env)

```env
# Azure AD
TENANT_ID=xxx
CLIENT_ID=xxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
```

### Agent Configuration (langgraph_agent/config.py)

```python
CLAUDE_MODEL = "claude-sonnet-4-20250514"
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True
```

## Error Handling

### Levels of Error Handling

1. **User Interface**: Catches all exceptions, displays friendly messages
2. **Agent**: Handles tool execution errors, retries with different approaches
3. **MCP Server**: Returns error messages as TextContent
4. **Graph Client**: HTTP error handling with detailed logging
5. **Auth Layer**: Token refresh, re-authentication on failure

### Common Error Scenarios

| Error | Cause | Handling |
|-------|-------|----------|
| API Key Invalid | Wrong ANTHROPIC_API_KEY | Fail fast at initialization |
| Auth Failure | Azure AD issues | Browser popup for re-auth |
| Token Expired | Cached token expired | Silent refresh or re-auth |
| Graph API 401 | Permission issues | Clear cache, re-authenticate |
| No Results | Search returned empty | Agent rephrases or asks for clarification |

## Performance Considerations

### Token Caching
- Reduces authentication overhead
- Browser popup only on first run or expiry
- ~24 hour token lifetime (configurable by Azure AD)

### Search Optimization
- Field selection reduces payload size
- Pagination limits result set
- Page size configurable per query

### Agent Efficiency
- Claude Sonnet 4.5 optimized for tool use
- Parallel tool calls when supported
- Early termination when answer is found

## Security Considerations

### Credentials
- API keys in `.env` (not in git)
- Token cache is local file (not encrypted by default)
- Azure AD handles OAuth flow securely

### Permissions
- Mail.Read scope (read-only)
- No write or delete capabilities
- User consent required

### Network
- MCP server runs locally (no network exposure)
- HTTPS for all Microsoft Graph calls
- HTTPS for Anthropic API calls

## Future Enhancements

### Potential Improvements

1. **Email Writing**: Add Mail.Send scope and tools
2. **Advanced Search**: Date filters, folder filters, attachment type filters
3. **Attachment Download**: Extend tools to download attachments
4. **Conversation Threading**: Track conversation IDs and thread emails
5. **Calendar Integration**: Add calendar search and meeting tools
6. **Multi-Account**: Support multiple mailbox authentication
7. **Streaming**: Real-time response streaming to UI
8. **Memory**: Persist conversation context across sessions
9. **RAG**: Index email content for semantic search
10. **Subprocess MCP**: Run MCP server as separate process

### Scalability Considerations

Current design is single-user, local execution. For multi-user:
- Deploy MCP server as network service
- Add authentication middleware
- Use connection pooling for Graph API
- Consider rate limiting

## Testing Strategy

### Unit Tests
- MCP server tool handlers
- Graph client search methods
- Authentication token handling

### Integration Tests
- End-to-end agent queries
- MCP client-server communication
- Graph API integration (with test account)

### Manual Testing
- Interactive mode conversation flows
- Various search query patterns
- Error recovery scenarios
- Authentication edge cases

## Maintenance

### Dependencies to Monitor
- `langgraph`: Breaking changes in workflow API
- `langchain-anthropic`: Claude model updates
- `mcp`: Protocol changes
- `msal`: Authentication flow updates
- `anthropic`: API versioning

### Logging
- INFO level: Agent decisions, tool calls
- ERROR level: Failures, exceptions
- Configure via Python logging

### Monitoring
- Track API usage (Anthropic costs)
- Monitor Graph API rate limits
- Watch for authentication failures

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [Anthropic API](https://docs.anthropic.com/)
- [MSAL Python](https://msal-python.readthedocs.io/)
