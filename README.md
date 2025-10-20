# Email Reader - Outlook Email Search Tools

A Microsoft Graph API-based email reader with two interfaces:
1. **Interactive CLI** - Manual email exploration
2. **LangGraph Agent** - AI-powered email search using Claude Sonnet 4.5

Both tools authenticate via Azure AD and provide email exploration capabilities for Outlook/Microsoft 365 mailboxes.

## Features

### Interactive CLI (Original)
- Interactive email-by-email exploration
- Search by recipient with pagination
- Attachment downloading to temporary directories
- HTML email body cleaning
- Email processing tracker (avoid duplicates)

### LangGraph Agent (New)
- **Natural language queries** - Ask questions in plain English
- **AI-powered search** - Claude Sonnet 4.5 understands intent and orchestrates searches
- **MCP-based architecture** - Extensible tool-based system
- **Multi-step reasoning** - Agent can perform complex searches and analysis

## Architecture

### Interactive CLI
```
User → main.py → GraphClient → Microsoft Graph API
         ↓
    InteractiveAuth (MSAL + Token Cache)
```

### LangGraph Agent
```
User → run_agent.py → LangGraph Agent (Claude Sonnet 4.5)
                            ↓
                       MCP Server (Local)
                            ↓
                       GraphClient → Microsoft Graph API
                            ↓
                       InteractiveAuth (MSAL + Token Cache)
```

## Setup

### 1. Azure AD Application Registration

Create an Azure AD app registration with:
- **Application type**: Public client application
- **Redirect URI**: `http://localhost` (for MSAL interactive auth)
- **API Permissions**: `Mail.Read` (Microsoft Graph)

### 2. Environment Configuration

Create a `.env` file with your credentials:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
```

Required environment variables:

```env
# Azure AD Configuration (required for both CLI and Agent)
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here

# Anthropic API Configuration (required for LangGraph Agent only)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**How to get your Anthropic API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key

### 3. Install Dependencies

#### For Interactive CLI only:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### For LangGraph Agent (includes CLI dependencies):
```bash
# Use the setup script (recommended)
./setup_agent.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-agent.txt
```

## Usage

### Interactive CLI

Run the original interactive email explorer:

```bash
python main.py
```

This opens an interactive session where you can:
- Search for emails by recipient
- Browse emails one-by-one
- View full email content and attachments
- Skip or continue through results

### LangGraph Agent

#### Interactive Mode

Run the agent in conversational mode:

```bash
python run_agent.py
```

Example queries you can try:
- "Find emails about project updates from last week"
- "Search for emails with attachments about the budget"
- "Show me emails from john@example.com about meetings"
- "Find all emails mentioning 'quarterly review'"

#### Single Query Mode

Run a single query and exit:

```bash
python run_agent.py "Find emails about the maintenance project"
```

## How It Works

### Authentication

Both tools use **MSAL (Microsoft Authentication Library)** with interactive browser authentication:

1. **First Run**: A browser window opens for you to sign in with your Microsoft account
2. **Token Caching**: Your authentication token is cached in `token_cache.bin`
3. **Subsequent Runs**: Token is reused automatically (no browser popup)
4. **Token Refresh**: Automatic silent refresh when tokens expire

The authentication flow uses `http://localhost` as the redirect URI, which must be configured in your Azure AD app.

### Email Search

The tools use Microsoft Graph API's `$search` parameter with support for:
- **Match modes**: `raw`, `single`, `and`, `or`, `phrase`
- **Pagination**: Configurable page sizes
- **Field selection**: Optimized queries with specific fields
- **HTML cleaning**: BeautifulSoup-based HTML to plain text conversion

### LangGraph Agent Flow

1. User provides a natural language query
2. Claude Sonnet 4.5 analyzes the query and determines which tools to use
3. Agent calls MCP tools (search_emails, get_email_details, list_attachments)
4. MCP server executes Graph API calls with cached authentication
5. Results are returned to Claude for analysis and formatting
6. Agent provides a natural language response to the user

### MCP Server

The Model Context Protocol (MCP) server runs locally and exposes three tools:

1. **search_emails**: Search mailbox with flexible query modes
2. **get_email_details**: Retrieve full email content by ID
3. **list_email_attachments**: List attachment metadata

The MCP server authenticates once on startup (browser popup if no cached token), then serves tool requests from the agent.

## Project Structure

```
email-reader/
├── auth_interactive.py       # MSAL interactive authentication
├── auth.py                    # MSAL device flow authentication (fallback)
├── config.py                  # Azure AD configuration
├── graph_client.py            # Microsoft Graph API client
├── parsed_email_tracker.py   # Email processing tracker
├── main.py                    # Interactive CLI entry point
├── run_agent.py              # LangGraph agent entry point
├── setup_agent.sh            # Agent setup script
├── mcp_server/
│   ├── __init__.py
│   ├── server.py             # MCP server implementation
│   └── config.json           # MCP server configuration
├── langgraph_agent/
│   ├── __init__.py
│   ├── config.py             # Agent configuration
│   ├── agent.py              # LangGraph agent implementation
│   └── mcp_client.py         # MCP client wrapper
├── requirements.txt          # CLI dependencies
├── requirements-agent.txt    # Agent dependencies (includes CLI)
└── .env                      # Environment configuration (not in git)
```

## Troubleshooting

### Authentication Issues

**Problem**: Browser doesn't open or authentication fails

**Solutions**:
- Ensure `http://localhost` is added as a redirect URI in Azure AD app
- Delete `token_cache.bin` and try again
- Check that CLIENT_ID and TENANT_ID are correct in `.env`

### API Key Issues

**Problem**: "ANTHROPIC_API_KEY not found" error

**Solution**:
- Ensure your `.env` file contains `ANTHROPIC_API_KEY=sk-ant-...`
- The API key should start with `sk-ant-`
- Verify the key is active at https://console.anthropic.com/

### Import Errors

**Problem**: ModuleNotFoundError for mcp, langgraph, etc.

**Solution**:
- Ensure virtual environment is activated: `source .venv/bin/activate`
- Install agent dependencies: `pip install -r requirements-agent.txt`
- Or run the setup script: `./setup_agent.sh`

### Graph API Errors

**Problem**: HTTP 401 or 403 errors from Graph API

**Solution**:
- Verify `Mail.Read` permission is granted in Azure AD app
- Ensure admin consent is granted (if required by your tenant)
- Delete `token_cache.bin` and re-authenticate

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Adding New MCP Tools

1. Add tool definition in `mcp_server/server.py` → `list_tools()`
2. Implement handler in `mcp_server/server.py` → `call_tool()`
3. Add wrapper method in `langgraph_agent/mcp_client.py`
4. Create LangChain tool in `langgraph_agent/agent.py` → `_setup_tools()`

### Agent Configuration

Edit `langgraph_agent/config.py` to customize:
- Claude model version
- Max iterations
- Verbosity level

## License

See LICENSE file for details.

## Contributing

1. Create a feature branch
2. Make your changes
3. Update tests and documentation
4. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Azure AD app configuration
- Verify all environment variables are set correctly
- Check logs for detailed error messages
