import React from 'react';

export default function BoundsControls({ onSearch, hasBounds, drawnBounds }) {
  return (
    <div className="controls-container">
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '14px', color: 'var(--muted-text)', marginBottom: '16px' }}>
          {drawnBounds 
            ? "Search destinations inside the drawn area."
            : "Search destinations inside the visible map area."}
        </p>

        <button 
          className="btn-primary auto-width" 
          onClick={onSearch}
          disabled={!hasBounds && !drawnBounds}
          style={{ opacity: (!hasBounds && !drawnBounds) ? 0.5 : 1, cursor: (!hasBounds && !drawnBounds) ? 'not-allowed' : 'pointer', marginBottom: '12px' }}
        >
          Search Area
        </button>
      </div>
    </div>
  );
}
