import { useState, useEffect } from 'react';
import { autocomplete } from '../api/destinations';

export default function useAutocomplete(query, delay = 300) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!query || query.trim() === '') {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await autocomplete(query, controller.signal);
        if (result.error) {
          setError('Failed to load suggestions');
          setSuggestions([]);
        } else {
          setSuggestions(result.data.data || []);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    }, delay);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, delay]);

  return { suggestions, loading, error, setSuggestions };
}
