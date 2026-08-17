export async function getHealth() {
  const start = performance.now();
  try {
    const response = await fetch('/api/v1/health/');
    const data = await response.json();
    return {
      status: response.status,
      duration: Math.round(performance.now() - start),
      data,
      error: !response.ok,
      url: '/api/v1/health/',
      method: 'GET'
    };
  } catch (error) {
    return {
      status: 0,
      duration: Math.round(performance.now() - start),
      data: { error: error.message },
      error: true,
      url: '/api/v1/health/',
      method: 'GET'
    };
  }
}

export async function autocomplete(query, signal) {
  const start = performance.now();
  const url = `/api/v1/destinations/autocomplete/?q=${encodeURIComponent(query)}`;
  try {
    const response = await fetch(url, { signal });
    const data = await response.json();
    return {
      status: response.status,
      duration: Math.round(performance.now() - start),
      data,
      error: !response.ok,
      url,
      method: 'GET'
    };
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    return {
      status: 0,
      duration: Math.round(performance.now() - start),
      data: { error: error.message },
      error: true,
      url,
      method: 'GET'
    };
  }
}

export async function searchDestinations(query, country) {
  const start = performance.now();
  let url = `/api/v1/destinations/search/?q=${encodeURIComponent(query)}`;
  if (country) {
    url += `&country=${encodeURIComponent(country)}`;
  }
  try {
    const response = await fetch(url);
    const data = await response.json();
    return {
      status: response.status,
      duration: Math.round(performance.now() - start),
      data,
      error: !response.ok,
      url,
      method: 'GET'
    };
  } catch (error) {
    return {
      status: 0,
      duration: Math.round(performance.now() - start),
      data: { error: error.message },
      error: true,
      url,
      method: 'GET'
    };
  }
}

export async function searchNearby(lat, lon, radius) {
  const start = performance.now();
  const url = `/api/v1/destinations/nearby/?lat=${lat}&lon=${lon}&radius=${radius}`;
  try {
    const response = await fetch(url);
    const data = await response.json();
    return {
      status: response.status,
      duration: Math.round(performance.now() - start),
      data,
      error: !response.ok,
      url,
      method: 'GET'
    };
  } catch (error) {
    return {
      status: 0,
      duration: Math.round(performance.now() - start),
      data: { error: error.message },
      error: true,
      url,
      method: 'GET'
    };
  }
}

export async function searchWithinBounds(north, south, east, west) {
  const start = performance.now();
  const url = `/api/v1/destinations/within-bounds/?north=${north}&south=${south}&east=${east}&west=${west}`;
  try {
    const response = await fetch(url);
    const data = await response.json();
    return {
      status: response.status,
      duration: Math.round(performance.now() - start),
      data,
      error: !response.ok,
      url,
      method: 'GET'
    };
  } catch (error) {
    return {
      status: 0,
      duration: Math.round(performance.now() - start),
      data: { error: error.message },
      error: true,
      url,
      method: 'GET'
    };
  }
}
