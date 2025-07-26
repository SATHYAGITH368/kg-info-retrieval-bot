const axios = require('axios');

class KnowledgeGraphAgent {
  constructor() {
    this.apiUrl = 'http://localhost:8003/a2a';
  }

  async query(userQuery) {
    try {
      let text = userQuery.trim();

      if (/^(satellite|radar|insitu)$/i.test(text)) {
        text = `build ${text.toLowerCase()}`;
      }

      const payload = {
        role: "user",
        content: {
          type: "text",
          text: text
        }
      };

      const response = await axios.post(
        this.apiUrl,
        payload,
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 300000
        }
      );

      const result = response.data;

      if (result && Array.isArray(result.parts) && result.parts[0]?.text) {
        return {
          success: true,
          response: result.parts[0].text,
          timestamp: new Date().toISOString()
        };
      } else {
        throw new Error('Invalid response format from KG Agent');
      }
    } catch (error) {
      console.error('KG Agent Error:', error.message);
      return {
        success: false,
        response: error.message,
        error: error,
        timestamp: new Date().toISOString()
      };
    }
  }
}

module.exports = KnowledgeGraphAgent;
