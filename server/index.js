const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
require('dotenv').config();

const AGUIHandler = require('./agui-handler');

const app = express();
const server = http.createServer(app);

// 🛠️ Increase timeout for long-running requests
server.timeout = 5 * 60 * 1000;           // 5 minutes
server.keepAliveTimeout = 5 * 60 * 1000; // 5 minutes
server.headersTimeout = 6 * 60 * 1000;   // 6 minutes (must > keepAliveTimeout)

const wss = new WebSocket.Server({ server });

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../client/build')));

// AG-UI Handler instance
const aguiHandler = new AGUIHandler();

// WebSocket connection handling
wss.on('connection', (ws) => {
  console.log('New WebSocket connection established');
  
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);
      const response = await aguiHandler.handleMessage(data);
      
      if (response) {
        ws.send(JSON.stringify(response));
      }
    } catch (error) {
      console.error('WebSocket message error:', error);
      ws.send(JSON.stringify({
        type: 'ERROR',
        payload: { message: 'Internal server error' }
      }));
    }
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});

// REST API endpoints for AG-UI
app.post('/api/agui/start-session', (req, res) => {
  try {
    const response = aguiHandler.startSession(req.body);
    console.log('Session started:', response.payload.sessionId);
    res.json(response);
  } catch (error) {
    console.error('Session start error:', error);
    res.status(500).json({ error: 'Failed to start session' });
  }
});

app.post('/api/agui/chat', async (req, res) => {
  try {
    const { message, sessionId } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // SSE for streaming
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    await aguiHandler.handleMessageStream(message, sessionId, (event) => {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    });

    res.end();
  } catch (error) {
    console.error('AG-UI chat error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/agui/chat', async (req, res) => {
  try {
    const { message, sessionId } = req.query;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    if (!sessionId) {
      return res.status(400).json({ error: 'Session ID is required' });
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    await aguiHandler.handleMessageStream(message, sessionId, (event) => {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    });

    res.end();
  } catch (error) {
    console.error('AG-UI chat error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/agui/status', (req, res) => {
  const status = aguiHandler.getStatus();
  res.json(status);
});

app.post('/api/agui/cancel', (req, res) => {
  const { sessionId } = req.body;
  aguiHandler.cancelSession(sessionId);
  res.json({ success: true });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/build/index.html'));
});

const PORT = process.env.PORT || 5001;
server.listen(PORT, () => {
  console.log(`AG-UI Server running on port ${PORT}`);
  console.log(`WebSocket server ready`);
  console.log(`React app will be served from http://localhost:${PORT}`);
});
