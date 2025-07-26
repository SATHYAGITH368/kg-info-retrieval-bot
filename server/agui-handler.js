const { v4: uuidv4 } = require('uuid');
const KnowledgeGraphAgent = require('./agents/knowledge-graph-agent');
const CoordinatorAgent = require('./agents/coordinator-agent');
const ContextualSearchAgent = require('./agents/context-search-agent');
const GeoAgent = require('./agents/geoagent'); // <-- Add GeoAgent

class AGUIHandler {
  constructor() {
    this.sessions = new Map();
    this.agents = {
      knowledgeGraph: new KnowledgeGraphAgent(),
      coordinator: new CoordinatorAgent(),
      contextualSearch: new ContextualSearchAgent(),
      geo: new GeoAgent() // <-- Register GeoAgent
    };
    this.activeSessions = new Set();
  }

  async handleMessage(data) {
    const { type, payload, sessionId } = data;
    
    switch (type) {
      case 'START_SESSION':
        return this.startSession(payload);
      
      case 'USER_MESSAGE':
        // --- GeoAgent Routing ---
        if (payload.method === 'geo') {
          const geoResult = await this.agents.geo.query(payload.query || payload);
          return {
            type: 'TEXT_MESSAGE_CONTENT',
            payload: {
              sessionId,
              role: 'assistant',
              agent: 'geo',
              content: geoResult.results,
              timestamp: new Date().toISOString()
            }
          };
        }
        // Default: use coordinator pipeline
        return this.handleUserMessage(payload, sessionId);
      
      case 'CANCEL_SESSION':
        return this.cancelSession(sessionId);
      
      default:
        return {
          type: 'ERROR',
          payload: { message: `Unknown message type: ${type}` }
        };
    }
  }

  async handleMessageStream(message, sessionId, streamCallback) {
    const session = this.sessions.get(sessionId) || this.createSession(sessionId);
    
    streamCallback({
      type: 'LIFECYCLE_SIGNAL',
      payload: {
        sessionId,
        event: 'SESSION_STARTED',
        timestamp: new Date().toISOString()
      }
    });

    streamCallback({
      type: 'TEXT_MESSAGE_CONTENT',
      payload: {
        sessionId,
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      }
    });

    try {
      await this.runCoordinatorAgent(message, sessionId, streamCallback);
    } catch (error) {
      console.error('Agent execution error:', error);
      streamCallback({
        type: 'ERROR',
        payload: {
          sessionId,
          message: 'Agent execution failed',
          error: error.message
        }
      });
    }

    streamCallback({
      type: 'LIFECYCLE_SIGNAL',
      payload: {
        sessionId,
        event: 'SESSION_COMPLETED',
        timestamp: new Date().toISOString()
      }
    });
  }

  async runCoordinatorAgent(message, sessionId, streamCallback) {
    const session = this.sessions.get(sessionId);
    
    streamCallback({
      type: 'TOOL_CALL_START',
      payload: {
        sessionId,
        toolName: 'coordinator_analysis',
        parameters: { message },
        timestamp: new Date().toISOString()
      }
    });

    const coordinatorResponse = await this.agents.coordinator.process(message, session);
    
    streamCallback({
      type: 'TEXT_MESSAGE_CONTENT',
      payload: {
        sessionId,
        role: 'assistant',
        agent: 'coordinator',
        content: coordinatorResponse.analysis,
        timestamp: new Date().toISOString()
      }
    });

    session.state = {
      ...session.state,
      coordinatorAnalysis: coordinatorResponse.analysis,
      lastUpdate: new Date().toISOString()
    };

    streamCallback({
      type: 'STATE_DELTA',
      payload: {
        sessionId,
        state: session.state,
        timestamp: new Date().toISOString()
      }
    });

    if (coordinatorResponse.needsKnowledgeGraph) {
      await this.runKnowledgeGraphAgent(coordinatorResponse.kgQuery, sessionId, streamCallback);
    }

    if (coordinatorResponse.needsContextualSearch) {
      await this.runContextualSearchAgent(coordinatorResponse.csQuery, sessionId, streamCallback);
    }

    if (coordinatorResponse.needsGeoAgent) {
      await this.runGeoAgent(coordinatorResponse.geoQuery, sessionId, streamCallback);
    }

    streamCallback({
      type: 'TOOL_CALL_END',
      payload: {
        sessionId,
        toolName: 'coordinator_analysis',
        result: coordinatorResponse,
        timestamp: new Date().toISOString()
      }
    });
  }

  async runKnowledgeGraphAgent(query, sessionId, streamCallback) {
    const session = this.sessions.get(sessionId);
    
    streamCallback({
      type: 'TOOL_CALL_START',
      payload: {
        sessionId,
        toolName: 'knowledge_graph_query',
        parameters: { query },
        timestamp: new Date().toISOString()
      }
    });

    try {
      const kgResponse = await this.agents.knowledgeGraph.query(query);
      
      streamCallback({
        type: 'TEXT_MESSAGE_CONTENT',
        payload: {
          sessionId,
          role: 'assistant',
          agent: 'knowledgeGraph',
          content: kgResponse.response,
          timestamp: new Date().toISOString()
        }
      });

      session.state = {
        ...session.state,
        knowledgeGraphResult: kgResponse.response,
        knowledgeGraphQuery: query,
        lastUpdate: new Date().toISOString()
      };

      streamCallback({
        type: 'STATE_DELTA',
        payload: {
          sessionId,
          state: session.state,
          timestamp: new Date().toISOString()
        }
      });

      streamCallback({
        type: 'TOOL_CALL_END',
        payload: {
          sessionId,
          toolName: 'knowledge_graph_query',
          result: kgResponse,
          timestamp: new Date().toISOString()
        }
      });

    } catch (error) {
      console.error('Knowledge Graph agent error:', error);
      streamCallback({
        type: 'ERROR',
        payload: {
          sessionId,
          toolName: 'knowledge_graph_query',
          message: 'Knowledge Graph query failed',
          error: error.message
        }
      });
    }
  }

  async runContextualSearchAgent(query, sessionId, streamCallback) {
    const session = this.sessions.get(sessionId);

    streamCallback({
      type: 'TOOL_CALL_START',
      payload: {
        sessionId,
        toolName: 'contextual_search_query',
        parameters: { query },
        timestamp: new Date().toISOString()
      }
    });

    try {
      const csResponse = await this.agents.contextualSearch.query(query);

      const results = Array.isArray(csResponse.results) ? csResponse.results : [];
      const content = results.length > 0
        ? results.map(r => `${r.chunk} (score: ${r.score?.toFixed(2) || 0})`).join('\n')
        : 'No relevant results found.';

      streamCallback({
        type: 'TEXT_MESSAGE_CONTENT',
        payload: {
          sessionId,
          role: 'assistant',
          agent: 'contextualSearch',
          content: content,
          timestamp: new Date().toISOString()
        }
      });

      session.state = {
        ...session.state,
        contextualSearchResult: results,
        contextualSearchQuery: query,
        lastUpdate: new Date().toISOString()
      };

      streamCallback({
        type: 'STATE_DELTA',
        payload: {
          sessionId,
          state: session.state,
          timestamp: new Date().toISOString()
        }
      });

      streamCallback({
        type: 'TOOL_CALL_END',
        payload: {
          sessionId,
          toolName: 'contextual_search_query',
          result: csResponse,
          timestamp: new Date().toISOString()
        }
      });

    } catch (error) {
      console.error('Contextual Search agent error:', error);
      streamCallback({
        type: 'ERROR',
        payload: {
          sessionId,
          toolName: 'contextual_search_query',
          message: 'Contextual Search query failed',
          error: error.message
        }
      });
    }
  }

  async runGeoAgent(query, sessionId, streamCallback) {
    const session = this.sessions.get(sessionId);

    streamCallback({
      type: 'TOOL_CALL_START',
      payload: {
        sessionId,
        toolName: 'geo_query',
        parameters: { query },
        timestamp: new Date().toISOString()
      }
    });

    try {
      const geoResponse = await this.agents.geo.query(query);

      streamCallback({
        type: 'TEXT_MESSAGE_CONTENT',
        payload: {
          sessionId,
          role: 'assistant',
          agent: 'geo',
          content: geoResponse.results,
          timestamp: new Date().toISOString()
        }
      });

      session.state = {
        ...session.state,
        geoResult: geoResponse.results,
        geoQuery: query,
        lastUpdate: new Date().toISOString()
      };

      streamCallback({
        type: 'STATE_DELTA',
        payload: {
          sessionId,
          state: session.state,
          timestamp: new Date().toISOString()
        }
      });

      streamCallback({
        type: 'TOOL_CALL_END',
        payload: {
          sessionId,
          toolName: 'geo_query',
          result: geoResponse,
          timestamp: new Date().toISOString()
        }
      });

    } catch (error) {
      console.error('Geo agent error:', error);
      streamCallback({
        type: 'ERROR',
        payload: {
          sessionId,
          toolName: 'geo_query',
          message: 'Geo query failed',
          error: error.message
        }
      });
    }
  }

  startSession(payload) {
    const sessionId = uuidv4();
    const session = this.createSession(sessionId);
    
    this.activeSessions.add(sessionId);
    
    return {
      type: 'SESSION_STARTED',
      payload: {
        sessionId,
        timestamp: new Date().toISOString()
      }
    };
  }

  createSession(sessionId) {
    const session = {
      id: sessionId,
      state: {
        messages: [],
        agents: [],
        lastUpdate: new Date().toISOString()
      },
      createdAt: new Date().toISOString()
    };
    
    this.sessions.set(sessionId, session);
    return session;
  }

  cancelSession(sessionId) {
    this.activeSessions.delete(sessionId);
    this.sessions.delete(sessionId);
    
    return {
      type: 'SESSION_CANCELLED',
      payload: {
        sessionId,
        timestamp: new Date().toISOString()
      }
    };
  }

  getStatus() {
    return {
      activeSessions: this.activeSessions.size,
      totalSessions: this.sessions.size,
      agents: Object.keys(this.agents),
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = AGUIHandler;