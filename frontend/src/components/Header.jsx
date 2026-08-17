import React from 'react';
import HealthIndicator from './HealthIndicator';

export default function Header() {
  return (
    <header className="header">
      <h1>Destination Search</h1>
      <HealthIndicator />
    </header>
  );
}
