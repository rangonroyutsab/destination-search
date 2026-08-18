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
  const [panTrigger, setPanTrigger] = useState(0);

  // Drawing state
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [drawnBounds, setDrawnBounds] = useState(null);

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
    setIsDrawingMode(false);
    setDrawnBounds(null);
  };

  const executeSearch = async (apiCall, shouldFit = false) => {
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
      if (shouldFit) {
        setShouldFitBounds(true);
      }
    }
  };

  const handleSearch = (query, country) => {
    executeSearch(() => searchDestinations(query, country), true);
  };

  const handleNearbySearch = () => {
    if (nearbyCenter) {
      executeSearch(() => searchNearby(nearbyCenter.lat, nearbyCenter.lng, nearbyRadius), true);
    }
  };

  const handleBoundsSearch = () => {
    const boundsToSearch = drawnBounds || currentBounds;
    if (boundsToSearch) {
      const { north, south, east, west } = boundsToSearch;
      executeSearch(() => searchWithinBounds(north, south, east, west), false);
    }
  };

  const handleMapClick = (lat, lng) => {
    setNearbyCenter({ lat, lng });
  };

  // Resizing layout
  const containerRef = useRef(null);
  const [leftPaneWidth, setLeftPaneWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!isResizing) return;
    
    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidthPercent = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      
      if (newWidthPercent >= 50 && newWidthPercent <= 80) {
        setLeftPaneWidth(newWidthPercent);
      }
    };
    
    const handleMouseUp = () => setIsResizing(false);
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
    };
  }, [isResizing]);

  return (
    <div className="app-container">
      <Header />
      <div 
        className="main-content"
        ref={containerRef}
        style={{ '--left-pane-width': `${leftPaneWidth}%` }}
      >
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
                onCenterChange={(lat, lng, shouldPan = false) => {
                  setNearbyCenter({ lat, lng });
                  if (shouldPan) {
                    setPanTrigger(prev => prev + 1);
                  }
                }}
                onRadiusChange={setNearbyRadius}
                onSearch={handleNearbySearch}
              />
            )}
            {activeMode === 'bounds' && (
              <BoundsControls 
                onSearch={handleBoundsSearch}
                hasBounds={!!currentBounds}
                drawnBounds={drawnBounds}
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

        <div 
          className={`resizer ${isResizing ? 'active' : ''}`}
          onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
        />

        <div className="right-pane" style={{ pointerEvents: isResizing ? 'none' : 'auto' }}>
          <DestinationMap 
            mode={activeMode}
            results={results}
            selectedDestination={selectedDestination}
            hoveredDestination={hoveredDestination}
            nearbyCenter={nearbyCenter}
            nearbyRadiusKm={nearbyRadius}
            panTrigger={panTrigger}
            onSelectDestination={setSelectedDestination}
            onMapClick={handleMapClick}
            onBoundsChange={setCurrentBounds}
            shouldFitBounds={shouldFitBounds}
            isDrawingMode={isDrawingMode}
            setIsDrawingMode={setIsDrawingMode}
            drawnBounds={drawnBounds}
            onDrawComplete={(bounds) => {
              setDrawnBounds(bounds);
              setIsDrawingMode(false);
            }}
            onClearDrawnArea={() => setDrawnBounds(null)}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
