import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// Create custom icons to distinguish selection and modes
const defaultIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const selectedIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const centerIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function MapController({ 
  mode, 
  results, 
  selectedDestination, 
  nearbyCenter, 
  onMapClick, 
  onBoundsChange,
  shouldFitBounds
}) {
  const map = useMap();
  const previousResultsRef = useRef(results);

  // Expose bounds on load and move
  useMapEvents({
    moveend: () => {
      if (mode === 'bounds' && onBoundsChange) {
        const bounds = map.getBounds();
        onBoundsChange({
          north: bounds.getNorth(),
          south: bounds.getSouth(),
          east: bounds.getEast(),
          west: bounds.getWest()
        });
      }
    },
    click: (e) => {
      if (mode === 'nearby' && onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    }
  });

  // Fit bounds when new results arrive in search mode
  useEffect(() => {
    if (mode === 'search' && shouldFitBounds && results && results.length > 0) {
      // Only fit bounds if results actually changed (new search)
      if (results !== previousResultsRef.current) {
        const bounds = L.latLngBounds(results.map(r => [r.location?.lat, r.location?.lon]));
        map.fitBounds(bounds, { padding: [50, 50] });
        previousResultsRef.current = results;
      }
    }
  }, [results, mode, shouldFitBounds, map]);

  // Pan to selected destination if it's out of view
  useEffect(() => {
    if (selectedDestination) {
      const latlng = L.latLng(selectedDestination.location?.lat, selectedDestination.location?.lon);
      if (!map.getBounds().contains(latlng)) {
        map.panTo(latlng);
      }
    }
  }, [selectedDestination, map]);

  return null;
}

export default function DestinationMap({
  mode,
  results,
  selectedDestination,
  hoveredDestination,
  nearbyCenter,
  nearbyRadiusKm,
  onSelectDestination,
  onMapClick,
  onBoundsChange,
  shouldFitBounds
}) {
  // Center of world as fallback
  const defaultCenter = [20, 0];
  const defaultZoom = 2;

  return (
    <MapContainer 
      center={defaultCenter} 
      zoom={defaultZoom} 
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapController 
        mode={mode}
        results={results}
        selectedDestination={selectedDestination}
        nearbyCenter={nearbyCenter}
        onMapClick={onMapClick}
        onBoundsChange={onBoundsChange}
        shouldFitBounds={shouldFitBounds}
      />

      {/* Render Nearby Center & Circle */}
      {mode === 'nearby' && nearbyCenter && (
        <>
          <Marker position={[nearbyCenter.lat, nearbyCenter.lng]} icon={centerIcon} />
          <Circle 
            center={[nearbyCenter.lat, nearbyCenter.lng]} 
            radius={nearbyRadiusKm * 1000} 
            pathOptions={{ color: '#12303A', fillColor: '#12303A', fillOpacity: 0.1 }} 
          />
        </>
      )}

      {/* Render Destination Markers */}
      {results && results.map((dest, idx) => {
        const isSelected = selectedDestination?.location?.lat === dest.location?.lat && selectedDestination?.location?.lon === dest.location?.lon;
        const isHovered = hoveredDestination?.location?.lat === dest.location?.lat && hoveredDestination?.location?.lon === dest.location?.lon;
        const active = isSelected || isHovered;

        return (
          <Marker
            key={`${dest.city}-${dest.country}-${idx}`}
            position={[dest.location?.lat, dest.location?.lon]}
            icon={active ? selectedIcon : defaultIcon}
            eventHandlers={{
              click: () => onSelectDestination(dest)
            }}
          >
            {isSelected && (
              <Popup>
                <div>
                  <strong>{dest.city}, {dest.country}</strong><br/>
                  {(dest.population !== null) && <span>Pop: {dest.population.toLocaleString()}<br/></span>}
                </div>
              </Popup>
            )}
          </Marker>
        );
      })}
    </MapContainer>
  );
}
