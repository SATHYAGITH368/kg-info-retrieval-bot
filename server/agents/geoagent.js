const axios = require('axios');

class GeoAgent {
  /**
   * Sends a query to the Python GeoAgent (InsituGeoAgent) A2A server.
   * @param {string|object} query - The user query or a payload object.
   * @returns {Promise<object>} - The response from the geo agent.
   */
  async query(query) {
    try {
      const response = await axios.post('http://localhost:8010/a2a', {
        content: {
          text: typeof query === 'string' ? query : JSON.stringify(query),
          type: 'text'
        },
        role: 'user'
      });

      return {
        results: response.data?.content?.text || ""
      };
    } catch (error) {
      console.error('GeoAgent query failed:', error.message);
      return {
        results: "",
        error: error.message
      };
    }
  }
}

module.exports = GeoAgent;
