import { useState } from 'react';

export default function SearchForm({ onSearch, isLoading }) {
  const [formData, setFormData] = useState({
    latitude: 43.77579,
    longitude: -79.20664,
    radius_km: 10,
    dietary: ['vegan'],
    cuisine: [],
    meal_types: [],
    price_max: null,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      setFormData(prev => ({
        ...prev,
        [name]: checked
          ? [...(prev[name] || []), value]
          : (prev[name] || []).filter(item => item !== value)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'latitude' || name === 'longitude' || name === 'radius_km' || name === 'price_max'
          ? parseFloat(value) || null
          : value
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Search Restaurants</h2>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Latitude(User)</label>
            <input
              type="number"
              name="latitude"
              value={formData.latitude}
              onChange={handleChange}
              step="0.0001"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Longitude(User)</label>
            <input
              type="number"
              name="longitude"
              value={formData.longitude}
              onChange={handleChange}
              step="0.0001"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Radius (km)</label>
          <input
            type="number"
            name="radius_km"
            value={formData.radius_km}
            onChange={handleChange}
            min="1"
            max="50"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Dietary</label>
          <div className="space-y-2">
            {['vegan', 'vegetarian', 'halal', 'kosher'].map(diet => (
              <label key={diet} className="flex items-center">
                <input
                  type="checkbox"
                  name="dietary"
                  value={diet}
                  checked={formData.dietary?.includes(diet)}
                  onChange={handleChange}
                  className="h-4 w-4"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">{diet}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>
    </form>
  );
}
