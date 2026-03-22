# Deploying Surfa MCP to Fly.io

This guide walks you through deploying your Surfa MCP server to Fly.io for remote access.

## Prerequisites

1. **Install Fly.io CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up / Login**
   ```bash
   fly auth signup  # or fly auth login
   ```

## Deployment Steps

### 1. Set Secrets

Your API keys should be stored as Fly.io secrets (not in fly.toml):

```bash
# Required: Your Surfa API key
fly secrets set SURFA_API_KEY=sk_live_your_key_here

# Optional: Enable dogfooding
fly secrets set SURFA_INGEST_KEY=sk_live_your_ingest_key_here
```

### 2. Deploy

```bash
# First deployment (creates the app)
fly launch --no-deploy

# Deploy
fly deploy
```

### 3. Check Status

```bash
# View logs
fly logs

# Check app status
fly status

# Open in browser
fly open
```

Your MCP will be available at: `https://surfa-mcp.fly.dev`

## Configuration

### Custom App Name

Edit `fly.toml`:
```toml
app = "your-custom-name"
```

### Region

Change the region in `fly.toml`:
```toml
primary_region = "iad"  # US East
# Other options: lax (US West), lhr (London), fra (Frankfurt), etc.
```

### Scaling

```bash
# Scale to 2 machines
fly scale count 2

# Change machine size
fly scale vm shared-cpu-1x  # 256MB RAM
fly scale vm shared-cpu-2x  # 512MB RAM
```

### Auto-scaling

The default config scales to zero when not in use (saves money):
```toml
min_machines_running = 0  # Scale to zero
auto_stop_machines = true
auto_start_machines = true
```

## Using Your Remote MCP

### With Claude Desktop

Update `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "surfa": {
      "url": "https://surfa-mcp.fly.dev"
    }
  }
}
```

### With ChatGPT

Add as a custom action with the URL: `https://surfa-mcp.fly.dev`

### With MCP Client Libraries

```python
from mcp import ClientSession
import httpx

async with ClientSession(
    httpx.AsyncClient(),
    "https://surfa-mcp.fly.dev"
) as session:
    result = await session.call_tool("get_analytics", {})
```

## Monitoring

### View Logs
```bash
fly logs
```

### Metrics
```bash
fly dashboard
```

### Health Check
```bash
curl https://surfa-mcp.fly.dev/health
```

## Troubleshooting

### Deployment Fails

Check logs:
```bash
fly logs
```

### App Won't Start

Verify secrets are set:
```bash
fly secrets list
```

### Slow Performance

Increase machine size:
```bash
fly scale vm shared-cpu-2x
```

## Costs

- **Free tier**: 3 shared-cpu-1x machines (256MB RAM each)
- **Pricing**: ~$2-5/month for a single always-on instance
- **Scale to zero**: Free when not in use!

## Security

### Environment Variables

Never commit secrets to git. Always use Fly.io secrets:
```bash
fly secrets set KEY=value
```

### HTTPS

Fly.io provides free HTTPS certificates automatically.

### Access Control

Add authentication if needed (not included by default).

## Next Steps

1. **Monitor usage** in your Surfa dashboard
2. **Enable dogfooding** with SURFA_INGEST_KEY
3. **Share URL** with your team
4. **Set up CI/CD** for automatic deployments

## Support

- Fly.io Docs: https://fly.io/docs
- FastMCP Docs: https://github.com/jlowin/fastmcp
- Surfa Docs: https://docs.surfa.dev
