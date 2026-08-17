import React from 'react';
import { formatPopulation } from '../utils/formatPopulation';

export default function DestinationCard({ destination, mode, isSelected, onClick, onMouseEnter, onMouseLeave }) {
  return (
    <div 
      className={`result-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(destination)}
      onMouseEnter={() => onMouseEnter && onMouseEnter(destination)}
      onMouseLeave={() => onMouseLeave && onMouseLeave(destination)}
    >
      <div className="result-card-header">
        <span className="result-title">{destination.city}, {destination.country}</span>
        {mode === 'search' && destination.score !== undefined && destination.score !== null && (
          <span className="result-metric">Relevance {destination.score.toFixed(2)}</span>
        )}
        {mode === 'nearby' && destination.distance_km && (
          <span className="result-metric">{destination.distance_km.toFixed(2)} km away</span>
        )}
      </div>
      <div className="result-details">
        <div>
          <div className="result-pop">{formatPopulation(destination.population)}</div>
          <div className="result-coords">
            {destination.location?.lat?.toFixed(4)}, {destination.location?.lon?.toFixed(4)}
          </div>
        </div>
      </div>
    </div>
  );
}
