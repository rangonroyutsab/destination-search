export default function ResultSkeleton() {
  return (
    <div className="results-list">
      {[1, 2, 3].map(i => (
        <div key={i} className="result-card" style={{ opacity: 0.7 }}>
          <div style={{ height: '20px', background: '#e2e6e8', width: '50%', marginBottom: '8px', borderRadius: '4px' }}></div>
          <div style={{ height: '14px', background: '#e2e6e8', width: '30%', marginBottom: '4px', borderRadius: '4px' }}></div>
          <div style={{ height: '14px', background: '#e2e6e8', width: '40%', borderRadius: '4px' }}></div>
        </div>
      ))}
    </div>
  );
}
