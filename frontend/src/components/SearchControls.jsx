import React, { useState, useRef, useEffect } from 'react';
import useAutocomplete from '../hooks/useAutocomplete';
import AutocompleteDropdown from './AutocompleteDropdown';

export default function SearchControls({ onSearch }) {
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const { suggestions, loading, setSuggestions } = useAutocomplete(query, 300);
  const containerRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setDropdownOpen(true);
  };

  const handleSelectSuggestion = (suggestion) => {
    setQuery(suggestion.city);
    setCountry(suggestion.country);
    setDropdownOpen(false);
    setSuggestions([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setDropdownOpen(false);
      onSearch(query.trim(), country.trim());
    }
  };

  return (
    <form className="controls-container" onSubmit={handleSubmit}>
      <div className="controls-row">
        <div className="input-group" ref={containerRef}>
          <label htmlFor="search-destination">Search destination</label>
          <input
            id="search-destination"
            type="text"
            className="input-field"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setDropdownOpen(true)}
            placeholder="e.g. Dhaka"
            autoComplete="off"
            required
          />
          {dropdownOpen && (query.trim() !== '') && (
            <AutocompleteDropdown 
              suggestions={suggestions}
              loading={loading}
              onSelect={handleSelectSuggestion}
            />
          )}
        </div>
        
        <div className="input-group">
          <label htmlFor="search-country">Country (Optional)</label>
          <input
            id="search-country"
            type="text"
            className="input-field"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder="e.g. Bangladesh"
          />
        </div>

        <button type="submit" className="btn-primary auto-width">
          Search
        </button>
      </div>
    </form>
  );
}
