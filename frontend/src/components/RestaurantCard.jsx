export default function RestaurantCard({ restaurant, isSelected, onSelect }) {
  const handleClick = () => {
    console.log('🍽️ Restaurant ID:', restaurant.restaurant_id);
    onSelect(restaurant);
  };

  return (
    <div
      onClick={handleClick}
      className={`p-4 border-l-4 cursor-pointer transition ${
        isSelected
          ? 'bg-purple-50 dark:bg-purple-900 border-l-purple-600'
          : 'bg-white dark:bg-gray-800 border-l-gray-200 dark:border-l-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
      }`}
    >
      <h3 className="font-semibold text-gray-900 dark:text-white">{restaurant.name}</h3>

      <div className="mt-2 flex flex-wrap gap-2">
        {restaurant.cuisine.map(c => (
          <span key={c} className="inline-block text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
            {c}
          </span>
        ))}
      </div>

      <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
        <div>📍 {restaurant.distance_km} km away</div>
        <div>⭐ {restaurant.rating.toFixed(1)} rating</div>
        <div>💰 ${restaurant.price_max} max</div>
      </div>

      <div className="mt-2 flex gap-2">
        {restaurant.has_parking && <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">🅿️ Parking</span>}
        {restaurant.has_live_music && <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded">🎵 Live Music</span>}
      </div>
    </div>
  );
}
