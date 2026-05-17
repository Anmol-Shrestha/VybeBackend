const API_BASE_URL = 'http://localhost:8000/api';

export async function searchRestaurants(params) {
  const response = await fetch(`${API_BASE_URL}/restaurants/search?bypass_hours=true`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return await response.json();
}
