import { useState } from 'react';
import SearchForm from './components/SearchForm';
import RestaurantCard from './components/RestaurantCard';
import RestaurantMap from './components/RestaurantMap';
import VectorSearchContainer from './components/VectorSearchContainer';
import { searchRestaurants } from './api/restaurants';

export default function App() {
  const [restaurants, setRestaurants] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [searchLocation, setSearchLocation] = useState({ latitude: 43.77579, longitude: -79.20664 });
  const [radius, setRadius] = useState(10);

  const handleSearch = async (formData) => {
    setIsLoading(true);
    setError('');
    try {
      const results = await searchRestaurants(formData);
      setRestaurants(results);
      setSearchLocation({ latitude: formData.latitude, longitude: formData.longitude });
      setRadius(formData.radius_km);
      setSelectedRestaurant(null);
    } catch (err) {
      setError(`Failed to search: ${err.message}`);
      setRestaurants([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-screen flex bg-gray-100 dark:bg-gray-950">
      {/* Left Sidebar - Filter Search */}
      <div className="w-80 bg-white dark:bg-gray-900 shadow-lg flex flex-col overflow-hidden border-r border-gray-200 dark:border-gray-700">
        <SearchForm onSearch={handleSearch} isLoading={isLoading} />

        {error && (
          <div className="px-6 py-3 bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Results List */}
        {restaurants.length > 0 && (
          <>
            <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 font-semibold">
              Filter Results ({restaurants.length})
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {restaurants.map((restaurant) => (
                  <RestaurantCard
                    key={restaurant.restaurant_id}
                    restaurant={restaurant}
                    isSelected={selectedRestaurant?.restaurant_id === restaurant.restaurant_id}
                    onSelect={setSelectedRestaurant}
                  />
                ))}
              </div>
            </div>
          </>
        )}

        {restaurants.length === 0 && !isLoading && (
          <div className="flex-1 p-6 text-center text-gray-500 dark:text-gray-400 text-sm">
            No restaurants found
          </div>
        )}

        {isLoading && (
          <div className="flex-1 p-6 text-center text-gray-500 dark:text-gray-400">
            Searching...
          </div>
        )}
      </div>

      {/* Right Panel - Split between Vector Search and Map */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Vector Search Container */}
        {restaurants.length > 0 && (
          <div className="flex-1 overflow-hidden">
            <VectorSearchContainer
              restaurants={restaurants}
              onResults={setRestaurants}
            />
          </div>
        )}

        {/* Map Panel */}
        <div className={restaurants.length > 0 ? "h-96 border-t border-gray-200 dark:border-gray-700" : "flex-1"}>
          <RestaurantMap
            restaurants={restaurants}
            searchLocation={searchLocation}
            radius={radius}
            selectedRestaurant={selectedRestaurant}
            onMarkerSelect={setSelectedRestaurant}
          />
        </div>
      </div>
    </div>
  );
}
