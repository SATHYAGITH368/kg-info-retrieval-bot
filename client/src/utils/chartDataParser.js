export const parseStockLevelData = (responseText) => {
  try {
    // Try to find a JSON object in the response text
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return null;

    // Parse the JSON data
    const chartConfig = JSON.parse(jsonMatch[0]);
    
    // Check if it's a bar chart with at least one dataset
    if (chartConfig.type === 'bar' && chartConfig.data?.datasets?.length > 0) {
      const dataset = chartConfig.data.datasets[0];
      return {
        labels: chartConfig.data.labels,
        values: dataset.data,
        title: chartConfig.options?.plugins?.title?.text || chartConfig.title || '',
        datasetLabel: dataset.label || '',
        xAxisLabel: chartConfig.options?.scales?.x?.title?.text || '',
        yAxisLabel: chartConfig.options?.scales?.y?.title?.text || ''
      };
    }
    return null;
  } catch (error) {
    console.error('Error parsing stock level data:', error);
    return null;
  }
};

export const isStockLevelData = (responseText) => {
  // Check if the response contains chart configuration
  return responseText.includes('"type": "bar"') && 
         responseText.includes('"label": "Total Stock Levels"');
}; 