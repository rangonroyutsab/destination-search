export default function EmptyState({ mode }) {
  let msg = '';
  let subMsg = '';

  if (mode === 'search') {
    msg = 'No destinations found.';
    subMsg = 'Try another city, country, or spelling.';
  } else if (mode === 'nearby') {
    msg = 'No destinations found within the radius.';
    subMsg = 'Try another location or radius.';
  } else {
    msg = 'No destinations found in this area.';
    subMsg = 'Move or zoom the map and search again.';
  }

  return (
    <div className="empty-state">
      <strong>{msg}</strong>
      <p>{subMsg}</p>
    </div>
  );
}
