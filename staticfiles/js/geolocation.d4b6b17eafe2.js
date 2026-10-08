/**
 * Geolocation and manual location fallback system
 * Dona.Com — Community Free-Food Discovery Platform
 */

const GeolocationManager = {
  getStoredLocation() {
    const lat = sessionStorage.getItem('user_lat');
    const lng = sessionStorage.getItem('user_lng');
    const name = sessionStorage.getItem('user_location_name');
    if (lat && lng) {
      return {
        lat: parseFloat(lat),
        lng: parseFloat(lng),
        name: name || null,
        isManual: sessionStorage.getItem('user_location_manual') === 'true'
      };
    }
    return null;
  },

  setStoredLocation(lat, lng, name, isManual = false) {
    sessionStorage.setItem('user_lat', lat);
    sessionStorage.setItem('user_lng', lng);
    if (name) {
      sessionStorage.setItem('user_location_name', name);
    }
    sessionStorage.setItem('user_location_manual', isManual ? 'true' : 'false');
  },

  clearStoredLocation() {
    sessionStorage.removeItem('user_lat');
    sessionStorage.removeItem('user_lng');
    sessionStorage.removeItem('user_location_name');
    sessionStorage.removeItem('user_location_manual');
  },

  /**
   * Two-stage location request with accuracy verification & reverse geocode lookup:
   * Stage 1: High-accuracy GPS.
   * Stage 2: Fallback to network/IP-based coarse location if GPS fails/times out.
   */
  requestLocation(onSuccess, onError) {
    if (!navigator.geolocation) {
      if (onError) onError('Geolocation is not supported by your browser.');
      return;
    }

    const handleSuccess = async (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      const accuracy = position.coords.accuracy || 0; // in meters

      let locationName = null;
      try {
        const resp = await fetch(`/api/locations/reverse/?lat=${lat}&lng=${lng}`);
        const data = await resp.json();
        if (data.name) locationName = data.name;
      } catch (e) {
        console.warn('Reverse geocode lookup failed:', e);
      }

      GeolocationManager.setStoredLocation(lat, lng, locationName, false);

      const isCoarse = accuracy > 4000;
      if (onSuccess) {
        onSuccess({
          lat,
          lng,
          accuracy,
          isCoarse,
          locationName: locationName || 'Detected Location'
        });
      }
    };

    // Stage 1: High-accuracy GPS
    navigator.geolocation.getCurrentPosition(
      handleSuccess,
      (error) => {
        // Stage 2: Fallback to coarse network location
        if (error.code === error.TIMEOUT || error.code === error.POSITION_UNAVAILABLE) {
          navigator.geolocation.getCurrentPosition(
            handleSuccess,
            (fallbackError) => {
              let msg = 'Could not determine your location. Please search your city or village manually.';
              if (fallbackError.code === fallbackError.PERMISSION_DENIED) {
                msg = 'Location permission was denied. Please search your city or area manually.';
              }
              if (onError) onError(msg);
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 }
          );
        } else {
          const msg = 'Location permission was denied. Please search your city or area manually.';
          if (onError) onError(msg);
        }
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  }
};

document.addEventListener('DOMContentLoaded', () => {
  // "Find Free Food Near Me" CTA button handler.
  // Note: On pages with an embedded interactive map, map.js handles location centering.
  const nearMeBtns = document.querySelectorAll('.btn-near-me');
  const isMapPage = !!document.getElementById('fullDiscoveryMap') || !!document.getElementById('nearbyMap');

  nearMeBtns.forEach(btn => {
    if (isMapPage) return;

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Detecting location...</span>';
      btn.style.opacity = '0.7';

      GeolocationManager.requestLocation(
        (coords) => {
          let url = `/food/nearby/?lat=${coords.lat}&lng=${coords.lng}`;
          if (coords.locationName) {
            url += `&location_name=${encodeURIComponent(coords.locationName)}`;
          }
          window.location.href = url;
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

  // Manual location search modal autocomplete (available across all pages)
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

      // Display shimmer skeleton items immediately while fetching
      manualSearchResults.innerHTML = `
        <div class="skeleton-search-item">
          <div class="skeleton skeleton-title" style="width: 50%; height: 13px; margin-bottom: 4px;"></div>
          <div class="skeleton skeleton-text" style="width: 82%; height: 11px; margin-bottom: 0;"></div>
        </div>
        <div class="skeleton-search-item">
          <div class="skeleton skeleton-title" style="width: 62%; height: 13px; margin-bottom: 4px;"></div>
          <div class="skeleton skeleton-text" style="width: 75%; height: 11px; margin-bottom: 0;"></div>
        </div>
      `;

      debounceTimeout = setTimeout(async () => {
        try {
          const resp = await fetch(`/api/locations/search/?q=${encodeURIComponent(query)}`);
          const data = await resp.json();
          manualSearchResults.innerHTML = '';

          if (!data.results || data.results.length === 0) {
            manualSearchResults.innerHTML = '<div style="padding: 0.75rem; color: #64748b;">No matching places found. Try another city or town name (e.g., Palandur, Nagpur, Bhandara).</div>';
            return;
          }

          data.results.forEach(place => {
            const item = document.createElement('div');
            item.style.cssText = 'padding: 0.75rem; border-bottom: 1px solid #e2e8f0; cursor: pointer; transition: background 0.15s; font-size: 0.9rem;';
            const shortName = place.display_name.split(',')[0];
            item.innerHTML = `<strong>${shortName}</strong><div style="font-size: 0.8rem; color: #64748b;">${place.display_name}</div>`;
            item.addEventListener('mouseenter', () => item.style.backgroundColor = '#fef2f2');
            item.addEventListener('mouseleave', () => item.style.backgroundColor = 'transparent');
            item.addEventListener('click', () => {
              GeolocationManager.setStoredLocation(place.lat, place.lon, shortName, true);
              window.location.href = `/food/nearby/?lat=${place.lat}&lng=${place.lon}&location_name=${encodeURIComponent(shortName)}`;
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
