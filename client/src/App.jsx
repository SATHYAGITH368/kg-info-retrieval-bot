import React, { useState, useEffect } from 'react';
import ChartDisplay from './components/ChartDisplay';
import { parseStockLevelData, isStockLevelData } from './utils/chartDataParser';
import './styles/App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [chartData, setChartData] = useState(null);

  const handleMessage = (message) => {
    if (message.role === 'assistant') {
      if (isStockLevelData(message.content)) {
        const data = parseStockLevelData(message.content);
        if (data) {
          setChartData(data);
          // Remove the raw JSON from the message content
          const cleanedContent = message.content.replace(/\{[\s\S]*\}/, '')
            .replace(/Now, let's visualize this data[\s\S]*?understand the distribution of stock levels across different SKUs\./, '')
            .trim();
          message.content = cleanedContent;
        }
      }
    }
    setMessages(prev => [...prev, message]);
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
      </div>
      {chartData && (
        <div className="chart-container">
          <ChartDisplay data={chartData} />
        </div>
      )}
    </div>
  );
}

export default App; 