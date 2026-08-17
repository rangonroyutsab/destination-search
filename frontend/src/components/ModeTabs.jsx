import React from 'react';

export default function ModeTabs({ activeMode, onChange }) {
  const modes = [
    { id: 'search', label: 'Search' },
    { id: 'nearby', label: 'Nearby' },
    { id: 'bounds', label: 'Map Bounds' },
  ];

  return (
    <div className="mode-tabs">
      {modes.map(mode => (
        <button
          key={mode.id}
          className={`tab-button ${activeMode === mode.id ? 'active' : ''}`}
          onClick={() => onChange(mode.id)}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
