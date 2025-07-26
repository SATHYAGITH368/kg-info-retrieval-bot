const axios = require('axios');
const GeoAgent = require('./geoagent');

async function getLLMRoutedIntent(userMessage) {
  try {
    const apiKey = "AIzaSyAcc9r_l77Fv83C2qxadNV5CtGurMQHZcI";
    const apiUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

    const prompt = `
You are a routing assistant. Given a user message, decide which specialized agent is better suited to handle it.
Return ONLY one of these strings (lowercase, no punctuation):
- knowledge_graph
- contextual_search
- geo

If the user message asks about domains like satellite, insitu, radar, or about structured entities, relationships, nodes, edges, or a knowledge graph: knowledge_graph.
If the message involves locations, places, coordinates, cities, countries, mapping, or geoparsing: geo.
Otherwise (questions about unstructured text, document search, patterns, or contextual explanations): contextual_search.

User message: "${userMessage}"
Response:
    `.trim();

    const response = await axios.post(
      `${apiUrl}?key=${apiKey}`,
      {
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { maxOutputTokens: 10, temperature: 0 }
      },
      {
        headers: { "Content-Type": "application/json" }
      }
    );

    const intent = response.data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim().toLowerCase();
    console.debug(`LLM returned intent: ${intent}`);

    if (['knowledge_graph', 'contextual_search', 'geo'].includes(intent)) {
      return intent;
    }

    throw new Error('Invalid intent from LLM');
  } catch (error) {
    console.error('Gemini routing failed or returned invalid output. Falling back to rules.');
    const text = userMessage.toLowerCase();

    if (
      text.includes('graph') || text.includes('node') || text.includes('edge') ||
      text.includes('relationship') || text.includes('satellite') ||
      text.includes('insitu') || text.includes('radar')
    ) {
      return 'knowledge_graph';
    } else if (
      text.includes('latitude') || text.includes('longitude') || text.includes('lat') ||
      text.includes('lon') || text.includes('location') || text.includes('place') ||
      text.includes('city') || text.includes('country') || text.includes('geopars') ||
      text.includes('map')
    ) {
      return 'geo';
    } else {
      return 'contextual_search';
    }
  }
}

class CoordinatorAgent {
  constructor() {
    this.name = 'Coordinator Agent';
    this.description = 'Manages conversation flow and coordinates between Knowledge Graph, Contextual Search, and Geo agents';
    this.geo = new GeoAgent();
  }

  async process(message, session) {
    const timestamp = new Date().toISOString();
    const intent = await getLLMRoutedIntent(message);

    if (intent === 'knowledge_graph') {
      return {
        analysis: `Routing to Knowledge Graph Agent for: "${message}"`,
        needsKnowledgeGraph: true,
        needsContextualSearch: false,
        needsGeoAgent: false,
        kgQuery: message,
        intent,
        confidence: 1.0,
        timestamp
      };
    }

    if (intent === 'contextual_search') {
      return {
        analysis: `Routing to Contextual Search Agent for: "${message}"`,
        needsKnowledgeGraph: false,
        needsContextualSearch: true,
        needsGeoAgent: false,
        csQuery: message,
        intent,
        confidence: 1.0,
        timestamp
      };
    }

    if (intent === 'geo') {
      const geoResult = await this.geo.query(message);
      return {
        analysis: `Routing to Geo Agent for: "${message}"`,
        needsKnowledgeGraph: false,
        needsContextualSearch: false,
        needsGeoAgent: true,
        geoQuery: message,
        geoResult: geoResult.results,
        intent,
        confidence: 1.0,
        timestamp
      };
    }

    // fallback
    return {
      analysis: `Could not determine intent for: "${message}". Please clarify.`,
      needsKnowledgeGraph: false,
      needsContextualSearch: false,
      needsGeoAgent: false,
      intent: 'unknown',
      confidence: 0.0,
      timestamp
    };
  }

  async handleAgentResponse(agentName, response, session) {
    return {
      analysis: `I've received analysis from the ${agentName} agent:\n\n${response}`,
      agentResponse: response,
      timestamp: new Date().toISOString()
    };
  }

  getCapabilities() {
    return {
      name: this.name,
      description: this.description,
      capabilities: [
        'LLM-based dynamic routing',
        'Knowledge Graph, Contextual Search, or Geo delegation',
        'Extract and map geospatial data',
        'Conversation flow management',
        'Response coordination and synthesis'
      ],
      supportedIntents: ['knowledge_graph', 'contextual_search', 'geo'],
      timestamp: new Date().toISOString()
    };
  }

  updateSessionState(session, update) {
    if (!session.state) session.state = {};
    session.state = {
      ...session.state,
      coordinator: {
        ...session.state.coordinator,
        ...update
      },
      lastUpdate: new Date().toISOString()
    };
    return session.state;
  }
}

module.exports = CoordinatorAgent;
