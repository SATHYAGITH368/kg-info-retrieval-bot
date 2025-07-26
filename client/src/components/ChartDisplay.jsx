import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

const ChartDisplay = ({ data: chartData }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!chartData || !chartRef.current) return;

    // Destroy previous chart instance if it exists
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    // Create new chart
    const ctx = chartRef.current.getContext('2d');
    chartInstance.current = new Chart(ctx, {
      type: chartData.type,
      data: chartData.data,
      options: {
        ...(chartData.options || {}),
        responsive: true,
        maintainAspectRatio: false,
      }
    });

    // Cleanup function
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [chartData]);

  return (
    <div className="chart-wrapper" style={{ position: 'relative', height: '400px', width: '100%' }}>
      <canvas ref={chartRef}></canvas>
    </div>
  );
};

export default ChartDisplay; 