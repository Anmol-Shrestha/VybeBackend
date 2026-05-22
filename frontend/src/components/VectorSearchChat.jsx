import { useState, useRef, useEffect } from 'react';
import { vectorSearchRestaurants } from '../api/restaurants';

export default function VectorSearchChat({ restaurants, onResults, isLoading: parentLoading }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || parentLoading) return;

    const query = inputValue.trim();
    const restaurantIds = restaurants.map(r => r.restaurant_id);

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: query }]);
    setInputValue('');
    setIsLoading(true);

    try {
      if (restaurantIds.length === 0) {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: 'Please perform a search first to get restaurant options.'
        }]);
        return;
      }

      const results = await vectorSearchRestaurants(query, restaurantIds);
      onResults(results);

      // Add assistant message
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `Found ${results.length} restaurant${results.length !== 1 ? 's' : ''} matching "${query}"`
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `Error: ${err.message}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
            <p>💬 Ask me anything about these restaurants</p>
            <p className="text-xs mt-2">e.g., "vegan options", "good for dates", "late night dining"</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs px-4 py-2 rounded-lg ${
                msg.type === 'user'
                  ? 'bg-blue-500 dark:bg-blue-600 text-white rounded-br-none'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-none'
              }`}>
                {msg.content}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg rounded-bl-none">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Describe what you're looking for..."
            disabled={isLoading || parentLoading || restaurants.length === 0}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={isLoading || parentLoading || !inputValue.trim() || restaurants.length === 0}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '⟳' : '→'}
          </button>
        </div>
        {restaurants.length === 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Perform a manual search first to enable vector search
          </p>
        )}
      </form>
    </div>
  );
}
