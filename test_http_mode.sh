#!/bin/bash
# Test script for HTTP mode

echo "🧪 Testing Surfa MCP in HTTP mode..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "   Copy .env.example to .env and add your keys"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Start the server in background
echo "🚀 Starting MCP server..."
python -m surfa_mcp.server &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ Health check passed: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed"
    kill $SERVER_PID
    exit 1
fi

echo ""
echo "✅ Server is running on http://localhost:8000"
echo ""
echo "To test with Claude Desktop, update your config:"
echo '{'
echo '  "mcpServers": {'
echo '    "surfa": {'
echo '      "url": "http://localhost:8000"'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for Ctrl+C
wait $SERVER_PID
