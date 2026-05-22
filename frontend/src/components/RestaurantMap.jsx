import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

if (MAPBOX_TOKEN) {
  mapboxgl.accessToken = MAPBOX_TOKEN;
}

export default function RestaurantMap({ restaurants, searchLocation, radius, selectedRestaurant, onMarkerSelect }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  const popupsRef = useRef([]);

  useEffect(() => {
    if (!mapContainer.current) return;

    if (!MAPBOX_TOKEN) {
      mapContainer.current.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f3f4f6; color: #666;"><div style="text-align: center;"><p style="font-size: 18px; margin-bottom: 10px;">Mapbox token not configured</p><p style="font-size: 14px;">Add VITE_MAPBOX_TOKEN to .env file</p><p style="font-size: 12px; margin-top: 20px;">Get a free token at <a href="https://mapbox.com" target="_blank" rel="noopener noreferrer" style="color: #aa3bff;">mapbox.com</a></p></div></div>';
      return;
    }

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [searchLocation.longitude, searchLocation.latitude],
      zoom: 12,
    });

    // Add search location marker
    new mapboxgl.Marker({ color: '#aa3bff', scale: 1.5 })
      .setLngLat([searchLocation.longitude, searchLocation.latitude])
      .addTo(map.current);

    // Add radius circle as a GeoJSON source
    map.current.on('load', () => {
      map.current.addSource('radius-circle', {
        type: 'geojson',
        data: createCircle(searchLocation.latitude, searchLocation.longitude, radius),
      });

      map.current.addLayer({
        id: 'radius-circle-fill',
        type: 'fill',
        source: 'radius-circle',
        paint: {
          'fill-color': '#aa3bff',
          'fill-opacity': 0.1,
        },
      });

      map.current.addLayer({
        id: 'radius-circle-stroke',
        type: 'line',
        source: 'radius-circle',
        paint: {
          'line-color': '#aa3bff',
          'line-width': 2,
        },
      });
    });

    return () => {
      map.current?.remove();
    };
  }, [searchLocation, radius, MAPBOX_TOKEN]);

  // Add restaurant markers
  useEffect(() => {
    if (!map.current || !restaurants.length) return;

    // Clear existing markers and popups
    markersRef.current.forEach(marker => marker.remove());
    popupsRef.current.forEach(popup => popup.remove());
    markersRef.current = [];
    popupsRef.current = [];

    // Add new markers
    restaurants.forEach((restaurant) => {
      const el = document.createElement('div');
      el.className = 'w-8 h-8 bg-white rounded-full border-2 border-purple-600 cursor-pointer flex items-center justify-center text-sm font-bold';
      el.textContent = '📍';
      el.style.backgroundImage = "url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 30 30\"><circle cx=\"15\" cy=\"15\" r=\"12\" fill=\"white\" stroke=\"%23aa3bff\" stroke-width=\"2\"/><text x=\"15\" y=\"18\" text-anchor=\"middle\" font-size=\"14\" font-weight=\"bold\">🍽️</text></svg>')";
      el.style.backgroundSize = 'contain';
      el.style.backgroundRepeat = 'no-repeat';
      el.style.backgroundPosition = 'center';

      const marker = new mapboxgl.Marker(el)
        .setLngLat([restaurant.longitude, restaurant.latitude])
        .addTo(map.current);

      // Create popup with cuisine info
      const popup = new mapboxgl.Popup({ offset: 25, closeButton: false })
        .setHTML(`
          <div style="padding: 8px; font-size: 13px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${restaurant.name}</div>
            <div style="color: #666; font-size: 12px;">
              🍴 ${restaurant.cuisine.join(', ')}
            </div>
          </div>
        `);

      el.addEventListener('mouseenter', () => popup.addTo(map.current));
      el.addEventListener('mouseleave', () => popup.remove());
      el.addEventListener('click', () => onMarkerSelect(restaurant));

      markersRef.current.push(marker);
      popupsRef.current.push(popup);
    });
  }, [restaurants, onMarkerSelect]);

  // Highlight selected restaurant
  useEffect(() => {
    if (!map.current) return;

    const markerElements = mapContainer.current?.querySelectorAll('[style*="translate"]');
    markerElements?.forEach(el => {
      el.style.zIndex = '1';
    });

    if (selectedRestaurant && map.current) {
      map.current.flyTo({
        center: [selectedRestaurant.longitude, selectedRestaurant.latitude],
        zoom: 14,
        duration: 1000,
      });
    }
  }, [selectedRestaurant]);

  return (
    <div ref={mapContainer} className="w-full h-full rounded-lg overflow-hidden shadow-lg" />
  );
}

// Helper function to create a circle GeoJSON
function createCircle(lat, lng, radiusKm) {
  const points = 64;
  const coords = [];

  for (let i = 0; i < points; i++) {
    const angle = (i / points) * Math.PI * 2;
    const lat2 = lat + (radiusKm / 111) * Math.cos(angle);
    const lng2 = lng + (radiusKm / (111 * Math.cos(lat * Math.PI / 180))) * Math.sin(angle);
    coords.push([lng2, lat2]);
  }
  coords.push(coords[0]);

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [coords],
        },
      },
    ],
  };
}
