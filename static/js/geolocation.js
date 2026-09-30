/**
 * Geolocation and manual location fallback system
 * Free Food — Community Free-Food Discovery Platform
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
    const heroEl = document.getElementById('heroLocationName');
    if (heroEl && name) {
      heroEl.textContent = name;
    }
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

      const finalName = locationName || 'Current Location';
      GeolocationManager.setStoredLocation(lat, lng, finalName, false);

      const isCoarse = accuracy > 4000;
      if (onSuccess) {
        onSuccess({
          lat,
          lng,
          accuracy,
          isCoarse,
          locationName: finalName
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
              let msg = 'Could not determine your location. Please search your city or area manually.';
              if (fallbackError.code === fallbackError.PERMISSION_DENIED) {
                msg = 'Location permission was denied. Tap to search your area manually.';
              }
              if (onError) onError(msg);
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 }
          );
        } else {
          const msg = 'Location permission was denied. Tap to search your area manually.';
          if (onError) onError(msg);
        }
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  }
};

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Home Page Hero Location
  const heroLocationEl = document.getElementById('heroLocationName');
  const homeLocationBar = document.getElementById('homeLocationBar');

  if (homeLocationBar) {
    homeLocationBar.addEventListener('click', () => {
      openModal('manualLocationModal');
    });
  }

  if (heroLocationEl) {
    const urlParams = new URLSearchParams(window.location.search);
    const urlLat = urlParams.get('lat');
    const urlLng = urlParams.get('lng');
    const urlName = urlParams.get('location_name');
    const stored = GeolocationManager.getStoredLocation();

    if (urlName && urlName.trim()) {
      heroLocationEl.textContent = urlName.trim();
      if (urlLat && urlLng) {
        GeolocationManager.setStoredLocation(parseFloat(urlLat), parseFloat(urlLng), urlName.trim(), false);
      }
    } else if (stored && stored.name) {
      heroLocationEl.textContent = stored.name;
      // If home was loaded without ?lat= and ?lng=, refresh with stored coordinates
      if (!urlLat && !urlLng && window.location.pathname === '/') {
        urlParams.set('lat', stored.lat);
        urlParams.set('lng', stored.lng);
        urlParams.set('location_name', stored.name);
        window.location.replace(`${window.location.pathname}?${urlParams.toString()}`);
      }
    } else {
      // Auto-detect user's real GPS position
      heroLocationEl.textContent = 'Detecting location...';
      GeolocationManager.requestLocation(
        (coords) => {
          const detectedName = coords.locationName || 'Current Location';
          heroLocationEl.textContent = detectedName;
          if (!urlLat && window.location.pathname === '/') {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set('lat', coords.lat);
            newParams.set('lng', coords.lng);
            newParams.set('location_name', detectedName);
            window.location.replace(`${window.location.pathname}?${newParams.toString()}`);
          }
        },
        (errMsg) => {
          console.log('Location detection notice:', errMsg);
          heroLocationEl.textContent = 'Tap to set location';
        }
      );
    }
  }

  // Quick GPS detect button inside Manual Location Modal
  const btnDetectGPSInModal = document.getElementById('btnDetectGPSInModal');
  if (btnDetectGPSInModal) {
    btnDetectGPSInModal.addEventListener('click', () => {
      if (window.InteractionFeedback) {
        window.InteractionFeedback.setButtonLoading(btnDetectGPSInModal, 'Detecting location...');
      } else {
        btnDetectGPSInModal.disabled = true;
      }

      GeolocationManager.requestLocation(
        (coords) => {
          const placeName = coords.locationName || 'Current Location';
          GeolocationManager.setStoredLocation(coords.lat, coords.lng, placeName, false);
          closeModal('manualLocationModal');
          if (window.InteractionFeedback) {
            window.InteractionFeedback.restoreButton(btnDetectGPSInModal);
            window.InteractionFeedback.startTopProgress();
          } else {
            btnDetectGPSInModal.disabled = false;
          }

          if (window.location.pathname === '/') {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set('lat', coords.lat);
            newParams.set('lng', coords.lng);
            newParams.set('location_name', placeName);
            window.location.href = `${window.location.pathname}?${newParams.toString()}`;
          } else {
            window.location.href = `/food/nearby/?lat=${coords.lat}&lng=${coords.lng}&location_name=${encodeURIComponent(placeName)}`;
          }
        },
        (err) => {
          if (window.InteractionFeedback) {
            window.InteractionFeedback.setButtonError(btnDetectGPSInModal, 'Detection failed');
          } else {
            btnDetectGPSInModal.disabled = false;
          }
          if (typeof showToast === 'function') {
            showToast(err || 'Could not detect location. Please search area manually.', 'error');
          } else {
            alert(err || 'Could not detect location.');
          }
        }
      );
    });
  }

  // "Find Free Food Near Me" CTA button handler with immediate spinner feedback
  const nearMeBtns = document.querySelectorAll('.btn-near-me');
  const isMapPage = !!document.getElementById('fullDiscoveryMap') || !!document.getElementById('nearbyMap');

  nearMeBtns.forEach(btn => {
    if (isMapPage) return;

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.InteractionFeedback) {
        window.InteractionFeedback.setButtonLoading(btn, 'Finding food...');
      } else {
        btn.disabled = true;
      }

      GeolocationManager.requestLocation(
        (coords) => {
          if (window.InteractionFeedback) {
            window.InteractionFeedback.startTopProgress();
          }
          let url = `/food/nearby/?lat=${coords.lat}&lng=${coords.lng}`;
          if (coords.locationName) {
            url += `&location_name=${encodeURIComponent(coords.locationName)}`;
          }
          window.location.href = url;
        },
        (errorMsg) => {
          if (window.InteractionFeedback) {
            window.InteractionFeedback.setButtonError(btn, 'Location unavailable');
          } else {
            btn.disabled = false;
          }
          if (typeof showToast === 'function') {
            showToast(errorMsg, 'error');
          }
          openModal('manualLocationModal');
        }
      );
    });
  });

  // Manual location search modal autocomplete
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
            manualSearchResults.innerHTML = '<div style="padding: 0.75rem; color: #64748b;">No matching places found. Try another city or town name (e.g., Nagpur, Bhandara, Mumbai).</div>';
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
              closeModal('manualLocationModal');
              if (window.location.pathname === '/') {
                const newParams = new URLSearchParams(window.location.search);
                newParams.set('lat', place.lat);
                newParams.set('lng', place.lon);
                newParams.set('location_name', shortName);
                window.location.href = `${window.location.pathname}?${newParams.toString()}`;
              } else {
                window.location.href = `/food/nearby/?lat=${place.lat}&lng=${place.lon}&location_name=${encodeURIComponent(shortName)}`;
              }
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
