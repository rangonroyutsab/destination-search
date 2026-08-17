import React, { useState } from 'react';

export default function NearbyControls({ center, radius, onRadiusChange, onCenterChange, onSearch }) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const handleUseLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        onCenterChange(position.coords.latitude, position.coords.longitude);
      }, (err) => {
        alert('Failed to get location: ' + err.message);
      });
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  const handleLatChange = (e) => {
    const val = e.target.value === '' ? '' : parseFloat(e.target.value);
    onCenterChange(val, center?.lng || 0);
  };

  const handleLngChange = (e) => {
    const val = e.target.value === '' ? '' : parseFloat(e.target.value);
    onCenterChange(center?.lat || 0, val);
  };

  const latError = center && center.lat !== '' && (center.lat < -90 || center.lat > 90) ? 'Must be between -90 and 90' : null;
  const lngError = center && center.lng !== '' && (center.lng < -180 || center.lng > 180) ? 'Must be between -180 and 180' : null;
  const radiusError = radius === '' || radius <= 0 ? 'Must be a positive number' : null;
  
  const isValidCenter = center && center.lat !== '' && center.lng !== '' && !latError && !lngError;
  const hasErrors = latError || lngError || radiusError;
  const canSearch = isValidCenter && !radiusError;

  return (
    <div className="controls-container">
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '14px', color: 'var(--muted-text)', marginBottom: '12px' }}>
          Click the map to set a search center.
        </p>
        <button className="btn-secondary" onClick={handleUseLocation}>
          Use my location
        </button>
      </div>

      {center && isValidCenter && (
        <div style={{ marginBottom: '16px', fontSize: '14px' }}>
          <strong>Selected point</strong>
          <div style={{ color: 'var(--muted-text)', marginTop: '4px' }}>
            {Number(center.lat).toFixed(4)}, {Number(center.lng).toFixed(4)}
          </div>
        </div>
      )}

      <div style={{ marginBottom: '16px' }}>
        <button 
          className="dev-toggle" 
          onClick={() => setAdvancedOpen(!advancedOpen)}
          style={{ marginBottom: advancedOpen ? '12px' : '0' }}
        >
          Advanced coordinates {advancedOpen ? '▾' : '▸'}
        </button>
        {advancedOpen && (
          <div className="controls-row" style={{ marginTop: '8px', alignItems: 'flex-start' }}>
            <div className="input-group">
              <label>Latitude</label>
              <input 
                type="number" 
                className="input-field" 
                value={center ? center.lat : ''} 
                onChange={handleLatChange}
                step="any"
                style={{ borderColor: latError ? '#EF4444' : undefined }}
              />
              {latError && <div className="error-message">{latError}</div>}
            </div>
            <div className="input-group">
              <label>Longitude</label>
              <input 
                type="number" 
                className="input-field" 
                value={center ? center.lng : ''} 
                onChange={handleLngChange}
                step="any"
                style={{ borderColor: lngError ? '#EF4444' : undefined }}
              />
              {lngError && <div className="error-message">{lngError}</div>}
            </div>
          </div>
        )}
      </div>

      <div className="controls-row" style={{ alignItems: 'flex-start', marginTop: '16px' }}>
        <div className="input-group">
          <label>Radius (km)</label>
          <input 
            type="number"
            className="input-field" 
            value={radius} 
            onChange={(e) => {
              const val = e.target.value === '' ? '' : parseInt(e.target.value, 10);
              onRadiusChange(val);
            }}
            min="1"
            step="1"
            style={{ borderColor: radiusError ? '#EF4444' : undefined }}
          />
          {radiusError && <div className="error-message">{radiusError}</div>}
        </div>
        <button 
          className="btn-primary auto-width" 
          onClick={onSearch}
          disabled={!canSearch}
          style={{ opacity: !canSearch ? 0.5 : 1, cursor: !canSearch ? 'not-allowed' : 'pointer', marginTop: '20px' }}
        >
          Search Nearby
        </button>
      </div>
    </div>
  );
}
