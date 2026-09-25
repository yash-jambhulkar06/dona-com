/**
 * Geolocation and manual location fallback system
 * Community Free-Food Discovery Platform
 */

const GeolocationManager = {
  getStoredLocation() {
    const lat = sessionStorage.getItem('user_lat');
    const lng = sessionStorage.getItem('user_lng');
    if (lat && lng) {
      return { lat: parseFloat(lat), lng: parseFloat(lng) };
    }
    return null;
  },

  setStoredLocation(lat, lng) {
    sessionStorage.setItem('user_lat', lat);
    sessionStorage.setItem('user_lng', lng);
  },

  requestLocation(onSuccess, onError) {
    if (!navigator.geolocation) {
      if (onError) onError('Geolocation is not supported by your browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        GeolocationManager.setStoredLocation(lat, lng);
        if (onSuccess) onSuccess({ lat, lng });
      },
      (error) => {
        let msg = 'Location permission was denied or unavailable.';
        if (error.code === error.PERMISSION_DENIED) {
          msg = 'Location permission was denied. You can search your city or area manually.';
        }
        if (onError) onError(msg);
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 300000 }
    );
  }
};

document.addEventListener('DOMContentLoaded', () => {
  // Find Free Food Near Me CTA button handler
  const nearMeBtns = document.querySelectorAll('.btn-near-me');
  nearMeBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Detecting location...</span>';
      btn.style.opacity = '0.7';

      GeolocationManager.requestLocation(
        (coords) => {
          window.location.href = `/food/nearby/?lat=${coords.lat}&lng=${coords.lng}`;
        },
        (errorMsg) => {
          btn.innerHTML = originalText;
          btn.style.opacity = '1';
          showToast(errorMsg, 'error');
          openModal('manualLocationModal');
        }
      );
    });
  });

  // Manual location search input autocomplete
  const manualSearchInput = document.getElementById('manualLocationInput');
  const manualSearchResults = document.getElementById('manualSearchResults');
  let debounceTimeout = null;

  if (manualSearchInput && manualSearchResults) {
    manualSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      clearTimeout(debounceTimeout);
      if (query.length < 2) {
        manualSearchResults.innerHTML = '';
        return;
      }

      debounceTimeout = setTimeout(async () => {
        try {
          const resp = await fetch(`/api/locations/search/?q=${encodeURIComponent(query)}`);
          const data = await resp.json();
          manualSearchResults.innerHTML = '';
          
          if (!data.results || data.results.length === 0) {
            manualSearchResults.innerHTML = '<div style="padding: 0.75rem; color: #64748b;">No matching places found. Try another city or area name.</div>';
            return;
          }

          data.results.forEach(place => {
            const item = document.createElement('div');
            item.style.cssText = 'padding: 0.75rem; border-bottom: 1px solid #e2e8f0; cursor: pointer; transition: background 0.15s; font-size: 0.9rem;';
            item.innerHTML = `<strong>${place.display_name.split(',')[0]}</strong><div style="font-size: 0.8rem; color: #64748b;">${place.display_name}</div>`;
            item.addEventListener('mouseenter', () => item.style.backgroundColor = '#f1f5f9');
            item.addEventListener('mouseleave', () => item.style.backgroundColor = 'transparent');
            item.addEventListener('click', () => {
              GeolocationManager.setStoredLocation(place.lat, place.lon);
              window.location.href = `/food/nearby/?lat=${place.lat}&lng=${place.lon}&location_name=${encodeURIComponent(place.display_name.split(',')[0])}`;
            });
            manualSearchResults.appendChild(item);
          });
        } catch (err) {
          console.error('Location search error:', err);
        }
      }, 300);
    });
  }
});
