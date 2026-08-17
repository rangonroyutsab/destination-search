import React, { useState, useRef, useEffect } from 'react';
import Header from './components/Header';
import ModeTabs from './components/ModeTabs';
import DestinationMap from './components/DestinationMap';
import DeveloperDetails from './components/DeveloperDetails';
import SearchControls from './components/SearchControls';
import NearbyControls from './components/NearbyControls';
import BoundsControls from './components/BoundsControls';
import DestinationList from './components/DestinationList';
import ResultSkeleton from './components/ResultSkeleton';
import EmptyState from './components/EmptyState';
import { searchDestinations, searchNearby, searchWithinBounds } from './api/destinations';

function App() {
  const [activeMode, setActiveMode] = useState('search');
  const [developerRequestInfo, setDeveloperRequestInfo] = useState(null);

  // Results state
  const [results, setResults] = useState([]);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [hoveredDestination, setHoveredDestination] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState(null);
  
  // Maps bounds and center
  const [shouldFitBounds, setShouldFitBounds] = useState(false);
  const [nearbyCenter, setNearbyCenter] = useState(null);
  const [nearbyRadius, setNearbyRadius] = useState(10);
  const [currentBounds, setCurrentBounds] = useState(null);

  // Latest request tracking to avoid stale updates
  const latestRequestId = useRef(0);

  const resetStateForSearch = () => {
    setResults([]);
    setSelectedDestination(null);
    setHoveredDestination(null);
    setError(null);
    setHasSearched(true);
    setShouldFitBounds(false);
  };

  const handleModeChange = (mode) => {
    setActiveMode(mode);
    setHasSearched(false);
    setResults([]);
  };

  const executeSearch = async (apiCall, isSearchMode = false) => {
    const reqId = ++latestRequestId.current;
    setLoading(true);
    resetStateForSearch();

    const result = await apiCall();
    
    if (reqId !== latestRequestId.current) {
      return;
    }

    setDeveloperRequestInfo(result);
    setLoading(false);

    if (result.error) {
      setError('Unable to load destinations. Please try again.');
    } else {
      setResults(result.data.data || []);
      if (isSearchMode) {
        setShouldFitBounds(true);
      }
    }
  };

  const handleSearch = (query, country) => {
    executeSearch(() => searchDestinations(query, country), true);
  };

  const handleNearbySearch = () => {
    if (nearbyCenter) {
      executeSearch(() => searchNearby(nearbyCenter.lat, nearbyCenter.lng, nearbyRadius), false);
    }
  };

  const handleBoundsSearch = () => {
    if (currentBounds) {
      const { north, south, east, west } = currentBounds;
      executeSearch(() => searchWithinBounds(north, south, east, west), false);
    }
  };

  const handleMapClick = (lat, lng) => {
    setNearbyCenter({ lat, lng });
  };

  return (
    <div className="app-container">
      <Header />
      <div className="main-content">
        <div className="left-pane">
          <ModeTabs activeMode={activeMode} onChange={handleModeChange} />
          
          <div className="controls-area">
            {activeMode === 'search' && (
              <SearchControls onSearch={handleSearch} />
            )}
            {activeMode === 'nearby' && (
              <NearbyControls 
                center={nearbyCenter}
                radius={nearbyRadius}
                onCenterChange={(lat, lng) => setNearbyCenter({ lat, lng })}
                onRadiusChange={setNearbyRadius}
                onSearch={handleNearbySearch}
              />
            )}
            {activeMode === 'bounds' && (
              <BoundsControls 
                onSearch={handleBoundsSearch}
                hasBounds={!!currentBounds}
              />
            )}
          </div>

          <div className="results-area">
            {error && (
              <div className="global-error">{error}</div>
            )}
            
            {loading && <ResultSkeleton />}
            
            {!loading && hasSearched && results.length === 0 && !error && (
              <EmptyState mode={activeMode} />
            )}

            {!loading && results.length > 0 && (
              <DestinationList 
                results={results}
                mode={activeMode}
                selectedDestination={selectedDestination}
                onSelect={setSelectedDestination}
                onHover={setHoveredDestination}
              />
            )}
          </div>

          <DeveloperDetails reqInfo={developerRequestInfo} />
        </div>
        <div className="right-pane">
          <DestinationMap 
            mode={activeMode}
            results={results}
            selectedDestination={selectedDestination}
            hoveredDestination={hoveredDestination}
            nearbyCenter={nearbyCenter}
            nearbyRadiusKm={nearbyRadius}
            onSelectDestination={setSelectedDestination}
            onMapClick={handleMapClick}
            onBoundsChange={setCurrentBounds}
            shouldFitBounds={shouldFitBounds}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
