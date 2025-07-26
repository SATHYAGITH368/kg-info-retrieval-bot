import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Database, Activity, ChevronDown, ChevronUp, Settings } from 'lucide-react';
import './App.css';
import EntityTree from './components/EntityTree';
import KGGraph from './components/KGGraph';

import GeoMap from './components/GeoMap';
import AudioRoom from './components/AudioRoom';






function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [showTechnicalEvents, setShowTechnicalEvents] = useState(false);
  const messagesEndRef = useRef(null);
  const [sharedState, setSharedState] = useState({});
  const [searchMethod, setSearchMethod] = useState("embedding");
  const speakText = (text) => {
  if ('speechSynthesis' in window && text) {
    window.speechSynthesis.cancel(); // cancel any ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
  }
};


  const suggestions = [
    "Build a knowledge graph for satellite data",
    "build knowledge graph for radar domain",
    "Build INSITU knowledge graph",
    "What entities are in the current knowledge graph?",
    "List relationships in the knowledge graph",
    "Geoparse Mumbai and Chennai",
    "Extract latitude and longitude for Delhi and Kolkata"
  ];

  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeSession = async () => {
    try {
      const response = await axios.post('/api/agui/start-session', {});
      if (response.data && response.data.payload && response.data.payload.sessionId) {
        setSessionId(response.data.payload.sessionId);
        setConnectionStatus('connected');
        console.log('Session initialized:', response.data.payload.sessionId);
      } else {
        console.error('Invalid session response:', response.data);
        setConnectionStatus('error');
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setConnectionStatus('error');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (message) => {
    if (!message.trim() || isLoading || !sessionId) return;

    console.log('Sending message:', message, 'Session ID:', sessionId);

    const userMessage = {
      id: Date.now(),
      type: 'TEXT_MESSAGE_CONTENT',
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // If user selects "geo" in dropdown, send method as "geo"
      let method = searchMethod;
      // Simple heuristic: if message contains "lat", "lon", "geoparse", "map", override to geo
      if (/\b(lat|lon|geoparse|map|extract latitude|extract longitude)\b/i.test(message)) {
        method = "geo";
      }
      const payload = JSON.stringify({ query: message, method });
      const eventSource = new EventSource(`/api/agui/chat?message=${encodeURIComponent(payload)}&sessionId=${sessionId}`);

      eventSource.onmessage = (event) => {
        console.log('Received event:', event.data);
        const data = JSON.parse(event.data);
        handleAGUIEvent(data);
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
        setIsLoading(false);
        setConnectionStatus('error');
      };

      eventSource.onclose = () => {
        console.log('EventSource closed');
        setIsLoading(false);
      };

    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
      setConnectionStatus('error');
    }
  };

  const handleAGUIEvent = (event) => {
    const { type, payload } = event;
    console.log('Handling AG-UI event:', type, payload);

    switch (type) {
      case 'TEXT_MESSAGE_CONTENT': {
        if (payload.role === 'user') return;
        const message = {
          id: Date.now() + Math.random(),
          type,
          role: payload.role,
          agent: payload.agent,
          content: payload.content,
          timestamp: payload.timestamp
        };
        setMessages(prev => [...prev, message]);
        if (
  payload.role !== 'user' &&
  ['knowledgeGraph', 'contextualSearch', 'geo'].includes(payload.agent)
) {
  speakText(payload.content);
}


        break;
      }
      case 'TOOL_CALL_START':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type,
          toolName: payload.toolName,
          parameters: payload.parameters,
          timestamp: payload.timestamp
        }]);
        break;
      case 'TOOL_CALL_END':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type,
          toolName: payload.toolName,
          result: payload.result,
          timestamp: payload.timestamp
        }]);
        break;
      case 'STATE_DELTA':
        setSharedState(payload.state);
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type,
          state: payload.state,
          timestamp: payload.timestamp
        }]);
        break;
      case 'LIFECYCLE_SIGNAL':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type,
          event: payload.event,
          timestamp: payload.timestamp
        }]);
        break;
      case 'ERROR':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type,
          message: payload.message,
          error: payload.error,
          timestamp: payload.timestamp
        }]);
        break;
      default:
        console.log('Unknown event type:', type);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputMessage);
    }
  };

  const isTechnicalEvent = (message) => {
    return ['TOOL_CALL_START', 'TOOL_CALL_END', 'STATE_DELTA', 'LIFECYCLE_SIGNAL'].includes(message.type);
  };

  const getVisibleMessages = () => {
    return messages.filter(msg => !isTechnicalEvent(msg) || showTechnicalEvents);
  };

  const renderMessage = (message) => {
    const { type, role, agent, content, timestamp, toolName, parameters, result, state, event, error } = message;

    switch (type) {
      case 'TEXT_MESSAGE_CONTENT': {
        // Special rendering for geo agent
if (agent === 'geo' && typeof content === 'string' && content.includes('Lat:')) {
  return (
    <div key={message.id} className={`message ${role}`}>
      <div className={`message-avatar agent-geo`}>
        <Bot size={20} />
      </div>
      <div className="message-content">
        <div className="agent-badge">geo</div>
        <pre>{content}</pre>
        <GeoMap results={content} />
        <div className="message-timestamp">
          {new Date(timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}



        const parts = [];
        let explanation = content;
        let graph_payload = null;

        if (content) {
          try {
            const parsedPayload = JSON.parse(content);
            if (parsedPayload.explanation) {
              explanation = parsedPayload.explanation;
            }
            graph_payload = parsedPayload.graph;
          } catch {
            // Not JSON? Use as-is
          }
        }

        parts.push(
          <ReactMarkdown key={'explainability'}>{explanation}</ReactMarkdown>
        );

        if (graph_payload) {
          const nodes = graph_payload.elements.nodes || [];
          const edges = graph_payload.elements.edges || [];
          const elements = [...nodes, ...edges];
          parts.push(
            <KGGraph key={'graph'} elements={elements} />
          );
        }

        return (
          <div key={message.id} className={`message ${role}`}>
            <div className={`message-avatar ${agent ? `agent-${agent}` : ''}`}>
              {role === 'user' ? <User size={20} /> : <Bot size={20} />}
            </div>
            <div className="message-content">
              {agent && <div className="agent-badge">{agent}</div>}
              {parts}
              <div className="message-timestamp">
                {new Date(timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        );
      }

      case 'TOOL_CALL_START':
        return (
          <div key={message.id} className="tool-call">
            <div className="tool-call-header">
              <Activity size={16} />
              Starting: {toolName}
            </div>
            <div className="tool-call-content">
              {JSON.stringify(parameters, null, 2)}
            </div>
          </div>
        );

      case 'TOOL_CALL_END':
        return (
          <div key={message.id} className="tool-call">
            <div className="tool-call-header">
              <Activity size={16} />
              Completed: {toolName}
            </div>
            <div className="tool-call-content">
              {JSON.stringify(result, null, 2)}
            </div>
          </div>
        );

      case 'STATE_DELTA':
        return (
          <div key={message.id} className="state-delta">
            <div className="state-delta-header">
              <Database size={16} />
              State Updated
            </div>
            <div className="tool-call-content">
              {JSON.stringify(state, null, 2)}
            </div>
          </div>
        );

      case 'LIFECYCLE_SIGNAL':
        return (
          <div key={message.id} className="lifecycle-signal">
            {event}
          </div>
        );

      case 'ERROR':
        return (
          <div key={message.id} className="error-message">
            <strong>Error:</strong> {error || message.message}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="container app-flex-layout">
      <div className="sidebar">
        <div className="header">
          <h1>Semantra.io</h1>
          <p>Interact with your custom agent.<br />Build, explore, and visualize knowledge graphs, contextualize, geoparse from your data.</p>
        </div>
        <div className="status-bar">
          <button
            className="technical-toggle"
            onClick={() => setShowTechnicalEvents(!showTechnicalEvents)}
          >
            <Settings size={16} />
            {showTechnicalEvents ? 'Hide' : 'Show'} Events
            {showTechnicalEvents ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
        <div className="sidebar-section">
          <h3>Sample Prompts</h3>
          <ul>
            {suggestions.map((suggestion, index) => (
              <li key={index}>
                <button
                  className="suggestion-button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={isLoading || !sessionId}
                >
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="main-content">
        <div style={{ padding: '10px', backgroundColor: '#f5f5f5' }}>
            <AudioRoom onTranscript={text => sendMessage(text)} />


        </div>

        
        <div className="chat-container">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="message">
                <div className="message-avatar agent-coordinator">
                  <Bot size={20} />
                </div>
                <div className="message-content">
                  <div className="agent-badge knowledge-graph">knowledge-graph</div>
                  <p>Welcome! I am your <b>Multi Agent</b>. I can help you:</p>
                  <ul>
                    <li><strong>Build knowledge graphs</strong> from CSV or text data</li>
                    <li><strong>Visualize entities and relationships</strong> in your domain</li>
                    <li><strong>Answer questions</strong> about the graph structure</li>
                    <li><strong>Export or explore</strong> the graph interactively</li>
                    <li><strong>Contextualize</strong> your queries with unstructured data</li>
                    <li><strong>Geoparse</strong> locations and plot them on a map</li>
                  </ul>
                  <p>Try a prompt like: <i>"Geoparse Mumbai and Chennai"</i></p>
                </div>
              </div>
            )}
            {sharedState.knowledgeGraphResult && (
              <div className="knowledge-graph-visualization">
                <h3>Knowledge Graph Visualization</h3>
                <div className="kg-graph-placeholder">
                  <pre style={{ whiteSpace: 'pre-wrap' }}>
                    {sharedState.knowledgeGraphResult}
                  </pre>
                </div>
                <div className="kg-ols4-tree">
                  <h4>Ontology Tree</h4>
                  <EntityTree />
                </div>
              </div>
            )}

            {getVisibleMessages().map(renderMessage)}
            {isLoading && (
              <div className="message">
                <div className="message-avatar">
                  <Bot size={20} />
                </div>
                <div className="message-content">
                  <div className="loading">
                    Processing your request
                    <div className="loading-dots">
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="input-container">
            <form className="input-form" onSubmit={(e) => { e.preventDefault(); sendMessage(inputMessage); }}>
              <select
                value={searchMethod}
                onChange={e => setSearchMethod(e.target.value)}
                disabled={isLoading || !sessionId}
                style={{ marginRight: 8 }}
              >
                <option value="embedding">Contextual</option>
                <option value="bm25">BM25</option>
                <option value="geo">Geo</option>
              </select>
              <input
                type="text"
                className="message-input"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={sessionId ? "Ask about MOSDAC, or try 'Geoparse Mumbai and Chennai'" : "Initializing session..."}
                disabled={isLoading || !sessionId}
              />
              <button
                type="submit"
                className="send-button"
                disabled={isLoading || !inputMessage.trim() || !sessionId}
              >
                <Send size={20} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;