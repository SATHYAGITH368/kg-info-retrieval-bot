import React from 'react';

const GeoMap = ({ results }) => {
  if (!results || typeof results !== 'string') return null;

  // Extract first "Lat: xx, Lon: yy" from result string
  const match = results.match(/Lat:\s*([-.\d]+),?\s*Lon:\s*([-.\d]+)/i);
  if (!match) return <div>No location found in result.</div>;

  const [_, lat, lon] = match;
  const mapSrc = `https://www.google.com/maps?q=${lat},${lon}&z=10&output=embed`;

  return (
    <div style={{ width: '100%', height: '400px', marginTop: '1rem' }}>
      <iframe
        title="Google Map"
        src={mapSrc}
        width="100%"
        height="100%"
        style={{ border: 0 }}
        allowFullScreen
        loading="lazy"
      />
    </div>
  );
};

export default GeoMap;

