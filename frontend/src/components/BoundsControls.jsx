import React from 'react';

export default function BoundsControls({ onSearch, hasBounds }) {
  return (
    <div className="controls-container">
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '14px', color: 'var(--muted-text)', marginBottom: '16px' }}>
          Search destinations inside the visible map area.
        </p>
        <button 
          className="btn-primary auto-width" 
          onClick={onSearch}
          disabled={!hasBounds}
          style={{ opacity: !hasBounds ? 0.5 : 1, cursor: !hasBounds ? 'not-allowed' : 'pointer' }}
        >
          Search This Area
        </button>
      </div>
    </div>
  );
}
