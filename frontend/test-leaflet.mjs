import L from 'leaflet';
try {
  const circle = L.circle([50, 50], { radius: 1000 });
  const bounds = circle.getBounds();
  console.log("Bounds:", bounds);
} catch (e) {
  console.error("Error:", e.message);
}
