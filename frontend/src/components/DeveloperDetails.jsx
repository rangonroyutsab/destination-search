import React, { useState } from 'react';

export default function DeveloperDetails({ reqInfo }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!reqInfo) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(reqInfo.data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="developer-details">
      <button className="dev-toggle" onClick={() => setOpen(!open)}>
        Developer details {open ? '▴' : '▾'}
      </button>

      {open && (
        <div className="dev-content">
          <div className="dev-meta">
            <span><strong>{reqInfo.method}</strong> {reqInfo.url}</span>
            <span>Status: <strong>{reqInfo.status}</strong></span>
            <span>Duration: <strong>{reqInfo.duration} ms</strong></span>
          </div>
          <div className="dev-response-wrapper">
            <button className="btn-secondary btn-small dev-copy" onClick={handleCopy}>
              {copied ? 'Response copied' : 'Copy Response'}
            </button>
            <pre className="dev-pre">
              {JSON.stringify(reqInfo.data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
