import { useState, useRef, useEffect } from 'react';
import { vectorSearchRestaurants } from '../api/restaurants';

export default function VectorSearchContainer({ restaurants, onResults }) {
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
    if (!inputValue.trim() || isLoading || restaurants.length === 0) return;

    const query = inputValue.trim();
    const restaurantIds = restaurants.map(r => r.restaurant_id);

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: query, timestamp: new Date() }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const results = await vectorSearchRestaurants(query, restaurantIds);
      onResults(results);

      // Add assistant message
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `Found ${results.length} restaurant${results.length !== 1 ? 's' : ''} matching "${query}"`,
        timestamp: new Date(),
        results
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `❌ Error: ${err.message}`,
        timestamp: new Date(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">🔍 Semantic Search</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Ask anything about the {restaurants.length} restaurants
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-4">💬</div>
              <p className="text-slate-600 dark:text-slate-400 font-medium">Ask me anything</p>
              <p className="text-sm text-slate-500 dark:text-slate-500 mt-2">
                Try: "vegan restaurants", "good for dates", "late night", "live music"
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg ${
                msg.type === 'user'
                  ? 'bg-blue-500 dark:bg-blue-600 text-white rounded-br-none'
                  : msg.isError
                  ? 'bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100 rounded-bl-none'
                  : 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-bl-none shadow-sm'
              }`}>
                <p className="text-sm">{msg.content}</p>
                <p className={`text-xs mt-1 ${
                  msg.type === 'user'
                    ? 'text-blue-100'
                    : msg.isError
                    ? 'text-red-700 dark:text-red-200'
                    : 'text-slate-500 dark:text-slate-400'
                }`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-4 py-3 rounded-lg rounded-bl-none shadow-sm">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Footer */}
      <div className="px-6 py-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 shadow-lg">
        {restaurants.length === 0 && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 bg-slate-100 dark:bg-slate-700 px-3 py-2 rounded">
            👈 Do a filter search first to enable semantic search
          </p>
        )}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Describe what you're looking for..."
            disabled={isLoading || restaurants.length === 0}
            className="flex-1 px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-slate-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim() || restaurants.length === 0}
            className="px-4 py-3 bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
          >
            {isLoading ? '⟳' : '→'}
          </button>
        </form>
      </div>
    </div>
  );
}
