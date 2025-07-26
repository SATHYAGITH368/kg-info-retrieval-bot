const axios = require('axios');

class ContextualSearchAgent {
  constructor() {
    this.apiUrl = 'http://localhost:8004/a2a';
  }

  async query(userQuery) {
    try {
      const payload = {
        role: "user",
        content: {
          type: "text",
          text: userQuery.trim()
        }
      };

      const response = await axios.post(
        this.apiUrl,
        payload,
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 30000
        }
      );

      const result = response.data;

      const text = result?.parts?.[0]?.text?.trim() || '';

      // try to parse as JSON if the text looks like it
      let results = [];
      try {
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed)) {
          results = parsed;
        } else {
          results = [{ chunk: text, score: null }];
        }
      } catch {
        results = [{ chunk: text, score: null }];
      }

      return {
        success: true,
        results,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('Contextual Search Agent Error:', error.message);
      return {
        success: false,
        response: error.message,
        error,
        timestamp: new Date().toISOString()
      };
    }
  }
}

module.exports = ContextualSearchAgent;
