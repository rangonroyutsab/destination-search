import React, { useEffect, useState } from 'react';

export default function AutocompleteDropdown({ suggestions, loading, onSelect }) {
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  useEffect(() => {
    setHighlightedIndex(-1);
  }, [suggestions]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex(prev => (prev > 0 ? prev - 1 : prev));
      } else if (e.key === 'Enter' && highlightedIndex >= 0) {
        e.preventDefault();
        onSelect(suggestions[highlightedIndex]);
      } else if (e.key === 'Escape') {
        onSelect(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [suggestions, highlightedIndex, onSelect]);

  if (loading) {
    return (
      <div className="autocomplete-dropdown">
        <div className="autocomplete-loading">Loading suggestions...</div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="autocomplete-dropdown">
      {suggestions.map((sug, index) => (
        <div
          key={sug.id || `${sug.city}-${sug.country}-${index}`}
          className={`autocomplete-item ${index === highlightedIndex ? 'highlighted' : ''}`}
          onClick={() => onSelect(sug)}
          onMouseEnter={() => setHighlightedIndex(index)}
        >
          <div className="autocomplete-city">{sug.city}</div>
          <div className="autocomplete-country">{sug.country}</div>
        </div>
      ))}
    </div>
  );
}
