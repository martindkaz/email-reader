# LangGraph Agent - Quick Start Guide

## 🚀 Setup (5 minutes)

### 1. Get Your Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy your key (starts with `sk-ant-`)

### 2. Configure Environment
```bash
# Add your API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

Your `.env` should now have:
```env
TENANT_ID=c9a10f99-8946-4bfd-b5b3-743f445affd6
CLIENT_ID=373fdcb8-d0d4-464d-8776-ab51b19d6f6a
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Install Dependencies
```bash
./setup_agent.sh
```

Or manually:
```bash
source .venv/bin/activate
pip install -r requirements-agent.txt
```

### 4. Run the Agent
```bash
python run_agent.py
```

## 💬 Usage Examples

### Interactive Mode (Recommended)
```bash
python run_agent.py
```

Then try:
```
You: Find emails about project updates
Agent: [Searches and returns results]

You: Show me the first one in detail
Agent: [Retrieves full email content]

You: Are there any with attachments?
Agent: [Searches for emails with attachments]
```

### Single Query Mode
```bash
python run_agent.py "Find emails from john@example.com about meetings"
```

## 📝 Example Queries

### Simple Searches
- "Find emails about project updates"
- "Search for emails from john@example.com"
- "Show me emails about budget"

### With Filters
- "Find emails with attachments about the quarterly report"
- "Search for emails mentioning 'deadline' from last week"

### Multi-Step
- "Find emails about the maintenance project and show me the most recent one"
- "Search for emails from sarah@example.com about meetings, then list any attachments"

## 🔧 Troubleshooting

### "ANTHROPIC_API_KEY not found"
✅ Solution: Make sure you added it to `.env` file (not `.env.example`)

### "Authentication failed" (Browser doesn't open)
✅ Solution:
1. Delete `token_cache.bin`
2. Run again - browser will open for Microsoft login
3. Once authenticated, token is cached for future use

### Module import errors
✅ Solution:
```bash
source .venv/bin/activate
pip install -r requirements-agent.txt
```

### Graph API 401 error
✅ Solution:
1. Verify Azure AD app has Mail.Read permission
2. Delete `token_cache.bin`
3. Re-authenticate

## 🎯 How It Works

```
Your Question
    ↓
Claude Sonnet 4.5 (understands intent)
    ↓
Chooses which tool to use:
  • search_emails
  • get_email_details
  • list_email_attachments
    ↓
MCP Server executes the tool
    ↓
Microsoft Graph API (your Outlook emails)
    ↓
Results back to Claude
    ↓
Natural language response to you
```

## 🔐 First Run Authentication

On first run, a browser window will open:
1. Sign in with your Microsoft account
2. Grant Mail.Read permission
3. Token is cached in `token_cache.bin`
4. Future runs use cached token (no browser popup)

## 📚 More Information

- **Full Documentation**: See [README.md](README.md)
- **Architecture Details**: See [dev_docs/langgraph_agent_architecture.md](dev_docs/langgraph_agent_architecture.md)
- **Implementation Summary**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## 🛠️ Commands Reference

```bash
# Interactive mode
python run_agent.py

# Single query
python run_agent.py "your query here"

# Setup
./setup_agent.sh

# Check environment
source .venv/bin/activate
python -c "from langgraph_agent.config import ANTHROPIC_API_KEY; print('✅ API key configured')"
```

## 💡 Tips

1. **Be specific**: "Find emails from john@example.com about Q4 budget" works better than "find budget emails"

2. **Ask follow-ups**: The agent remembers context within a session

3. **Use natural language**: You don't need to learn syntax, just ask naturally

4. **Check logs**: If something fails, check the terminal output for detailed error messages

## ⚡ Quick Test

After setup, test with:
```bash
python run_agent.py "Find any emails about test"
```

If you see Claude searching and returning results, you're all set! 🎉

## 📞 Need Help?

1. Check [README.md](README.md) troubleshooting section
2. Review logs for error details
3. Verify all environment variables are set
4. Make sure you're in the virtual environment: `source .venv/bin/activate`
