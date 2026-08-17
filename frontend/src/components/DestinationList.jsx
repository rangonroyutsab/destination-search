import React, { useEffect, useRef } from 'react';
import DestinationCard from './DestinationCard';

export default function DestinationList({ 
  results, 
  mode, 
  selectedDestination, 
  onSelect,
  onHover 
}) {
  const listRef = useRef(null);

  // Scroll into view if selected from map
  useEffect(() => {
    if (selectedDestination && listRef.current) {
      const selectedEl = listRef.current.querySelector('.result-card.selected');
      if (selectedEl) {
        selectedEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [selectedDestination]);

  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="results-list" ref={listRef}>
      {results.map((dest, idx) => (
        <DestinationCard
          key={`${dest.city}-${dest.country}-${idx}`} // using idx as fallback if no id
          destination={dest}
          mode={mode}
          isSelected={selectedDestination && selectedDestination.location?.lat === dest.location?.lat && selectedDestination.location?.lon === dest.location?.lon}
          onClick={onSelect}
          onMouseEnter={onHover}
          onMouseLeave={() => onHover(null)}
        />
      ))}
    </div>
  );
}
