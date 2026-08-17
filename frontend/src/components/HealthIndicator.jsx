import React, { useState, useEffect } from 'react';
import { getHealth } from '../api/destinations';

export default function HealthIndicator() {
  const [open, setOpen] = useState(false);
  const [healthData, setHealthData] = useState(null);
  const [status, setStatus] = useState('loading'); // loading, healthy, degraded, unavailable

  const fetchHealth = async () => {
    const result = await getHealth();
    let checks = null;

    if (result.data?.success) {
      checks = result.data.data?.checks;
    } else if (result.data?.error?.details) {
      checks = result.data.error.details;
    }

    if (checks) {
      const db = checks.database;
      const es = checks.elasticsearch;
      if (db === true && es === true) {
        setStatus('healthy');
      } else if (db === false && es === false) {
        setStatus('unavailable');
      } else {
        setStatus('degraded');
      }
      setHealthData(checks);
    } else {
      setStatus('unavailable');
      setHealthData(null);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleToggle = () => {
    if (!open) {
      fetchHealth(); // refresh on open
    }
    setOpen(!open);
  };

  const statusDisplay = status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <div className="health-indicator" onClick={handleToggle}>
      <div className={`health-dot ${status}`}></div>
      <span>{status === 'loading' ? 'Checking...' : statusDisplay}</span>

      {open && (
        <div className="health-popover" onClick={e => e.stopPropagation()}>
          <h3>API Status</h3>
          {healthData ? (
            <>
              <div className="health-stat">
                <span>Database</span>
                <span style={{ color: healthData.database === true ? '#10B981' : '#EF4444' }}>
                  {healthData.database === true ? 'Connected' : 'Error'}
                </span>
              </div>
              <div className="health-stat">
                <span>Elasticsearch</span>
                <span style={{ color: healthData.elasticsearch === true ? '#10B981' : '#EF4444' }}>
                  {healthData.elasticsearch === true ? 'Connected' : 'Error'}
                </span>
              </div>
            </>
          ) : (
            <div className="health-stat">Service unreachable</div>
          )}
        </div>
      )}
    </div>
  );
}
