/**
 * Map Integration using Leaflet + OpenStreetMap
 * Dona.Com — Community Free-Food Discovery Platform
 * Red Theme (Emoji-Free)
 */

const FoodMap = {
  _userMarker: null,    // holds the current "Your Location" circle marker instance
  _radiusCircle: null,  // holds the radius circle instance
  _mapInstance: null,   // reference to the main full-map Leaflet instance

  // ──────────────────────────────────────────────────────────────
  // Full Discovery Map (map_view page)
  // ──────────────────────────────────────────────────────────────
  initFullMap(containerId, pins) {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return null;

    // Default center: India or stored location or first pin
    const storedLoc = GeolocationManager.getStoredLocation();
    let center = [21.1458, 79.0882]; // Geographic center of India
    let zoom = 6;

    if (storedLoc) {
      center = [storedLoc.lat, storedLoc.lng];
      zoom = 12;
    } else if (pins && pins.length > 0) {
      center = [pins[0].lat, pins[0].lng];
      zoom = pins.length === 1 ? 14 : 10;
    }

    const map = L.map(containerId, { zoomControl: true }).setView(center, zoom);
    FoodMap._mapInstance = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Dismiss map skeleton screen placeholder if present
    const mapSkeleton = container.querySelector('.skeleton-map-wrapper');
    if (mapSkeleton) {
      setTimeout(() => {
        mapSkeleton.classList.add('is-hidden');
        setTimeout(() => mapSkeleton.remove(), 400);
      }, 300);
    }

    const bounds = [];

    // Plot all approved event pins (Red markers)
    pins.forEach(pin => {
      const marker = L.marker([pin.lat, pin.lng]).addTo(map);
      bounds.push([pin.lat, pin.lng]);

      const popupHtml = `
        <div class="map-popup-card">
          <div style="font-size: 0.75rem; font-weight: 700; color: #dc2626; text-transform: uppercase;">${pin.event_type}</div>
          <div class="map-popup-title">${pin.title}</div>
          <div class="map-popup-timing">Date: ${pin.date} | Time: ${pin.time}</div>
          <div style="font-size: 0.825rem; color: #475569; margin-bottom: 0.75rem;">Venue: ${pin.venue_name}</div>
          <div style="display: flex; gap: 0.5rem;">
            <a href="${pin.detail_url}" class="btn btn-primary btn-sm" style="flex: 1; text-align: center;">View Details</a>
            <a href="${pin.directions_url}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm" style="flex: 1; text-align: center;">Directions</a>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
    });

    if (!storedLoc && bounds.length > 1) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }

    // Plot stored user location if available
    if (storedLoc) {
      FoodMap._placeUserMarker(map, storedLoc.lat, storedLoc.lng, storedLoc.name || 'Your Location');
    }

    // Allow user to click anywhere on the map to set / move their location
    map.on('click', async (e) => {
      const lat = e.latlng.lat;
      const lng = e.latlng.lng;
      
      let locName = 'Selected Location';
      try {
        const resp = await fetch(`/api/locations/reverse/?lat=${lat}&lng=${lng}`);
        const data = await resp.json();
        if (data.name) locName = data.name;
      } catch (err) {}

      FoodMap._placeUserMarker(map, lat, lng, locName);
      GeolocationManager.setStoredLocation(lat, lng, locName, true);
      showToast(`Location set to: ${locName}`, 'success');
    });

    // Wire up "Center on My Location" button
    const locateBtn = document.querySelector('.btn-near-me');
    if (locateBtn) {
      locateBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const originalText = locateBtn.innerHTML;
        locateBtn.innerHTML = '<span>Detecting location...</span>';
        locateBtn.style.opacity = '0.7';

        GeolocationManager.requestLocation(
          (coords) => {
            locateBtn.innerHTML = originalText;
            locateBtn.style.opacity = '1';
            FoodMap._placeUserMarker(map, coords.lat, coords.lng, coords.locationName);
            map.flyTo([coords.lat, coords.lng], 13, { duration: 1.2 });

            if (coords.isCoarse) {
              showToast(
                `Detected network location (${coords.locationName}). If you are in Palandur or another area, use the search bar above to set exact place.`,
                'info'
              );
            } else {
              showToast(`Centered on ${coords.locationName}`, 'success');
            }
          },
          (errMsg) => {
            locateBtn.innerHTML = originalText;
            locateBtn.style.opacity = '1';
            showToast(errMsg, 'error');
            openModal('manualLocationModal');
          }
        );
      });
    }

    // Wire up the location search bar on the map page
    FoodMap._initMapSearchBar(map, 'mapLocationSearchInput', 'mapLocationSearchResults', (place) => {
      FoodMap._placeUserMarker(map, place.lat, place.lon, place.display_name.split(',')[0]);
      map.flyTo([place.lat, place.lon], 13, { duration: 1.2 });
      showToast(`Location set: ${place.display_name.split(',')[0]}`, 'success');
    });

    return map;
  },

  // ──────────────────────────────────────────────────────────────
  // Dedicated Nearby Events Map (nearby.html page)
  // ──────────────────────────────────────────────────────────────
  initNearbyMap(containerId, pins, userLat, userLng, radiusKm, locationName) {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return null;

    const lat = parseFloat(userLat);
    const lng = parseFloat(userLng);
    if (isNaN(lat) || isNaN(lng)) return null;

    const map = L.map(containerId, { zoomControl: true }).setView([lat, lng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    // Dismiss map skeleton screen placeholder if present
    const mapSkeleton = container.querySelector('.skeleton-map-wrapper');
    if (mapSkeleton) {
      setTimeout(() => {
        mapSkeleton.classList.add('is-hidden');
        setTimeout(() => mapSkeleton.remove(), 400);
      }, 300);
    }

    // 1. Draw search radius circle around user
    if (radiusKm) {
      const radiusMeters = parseFloat(radiusKm) * 1000;
      L.circle([lat, lng], {
        radius: radiusMeters,
        color: '#dc2626',
        fillColor: '#fee2e2',
        fillOpacity: 0.15,
        weight: 1.5,
        dashArray: '4, 6'
      }).addTo(map);
    }

    // 2. Add Draggable User Marker (Blue)
    const userMarker = L.circleMarker([lat, lng], {
      radius: 10,
      fillColor: '#2563eb',
      color: '#ffffff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95
    }).addTo(map);

    userMarker.bindPopup(`<strong>${locationName || 'Your Location'}</strong><br><span style="font-size:0.8rem;color:#64748b;">Click map to change location</span>`).openPopup();

    // 3. Plot Event Pins (Red markers)
    const bounds = [[lat, lng]];

    pins.forEach(pin => {
      const marker = L.marker([pin.lat, pin.lng]).addTo(map);
      bounds.push([pin.lat, pin.lng]);

      const distStr = pin.distance_km ? `<div style="font-size:0.8rem;font-weight:700;color:#16a34a;margin-bottom:0.25rem;">${pin.distance_km} km away</div>` : '';
      const popupHtml = `
        <div class="map-popup-card">
          <div style="font-size: 0.75rem; font-weight: 700; color: #dc2626; text-transform: uppercase;">${pin.event_type}</div>
          <div class="map-popup-title">${pin.title}</div>
          ${distStr}
          <div class="map-popup-timing">Date: ${pin.date} | Time: ${pin.time}</div>
          <div style="font-size: 0.825rem; color: #475569; margin-bottom: 0.75rem;">Venue: ${pin.venue_name}</div>
          <div style="display: flex; gap: 0.5rem;">
            <a href="${pin.detail_url}" class="btn btn-primary btn-sm" style="flex: 1; text-align: center;">View Details</a>
            <a href="${pin.directions_url}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm" style="flex: 1; text-align: center;">Directions</a>
          </div>
        </div>
      `;
      marker.bindPopup(popupHtml);
    });

    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }

    // Clicking map on nearby page allows setting new location and reloading
    map.on('click', async (e) => {
      const newLat = e.latlng.lat;
      const newLng = e.latlng.lng;
      let newName = 'Custom Location';
      try {
        const resp = await fetch(`/api/locations/reverse/?lat=${newLat}&lng=${newLng}`);
        const data = await resp.json();
        if (data.name) newName = data.name;
      } catch (err) {}

      GeolocationManager.setStoredLocation(newLat, newLng, newName, true);
      window.location.href = `/food/nearby/?lat=${newLat}&lng=${newLng}&radius=${radiusKm || '25'}&location_name=${encodeURIComponent(newName)}`;
    });

    return map;
  },

  // ──────────────────────────────────────────────────────────────
  // Place / update the user location circle marker
  // ──────────────────────────────────────────────────────────────
  _placeUserMarker(map, lat, lng, placeName = 'Your Location') {
    if (FoodMap._userMarker) {
      FoodMap._userMarker.setLatLng([lat, lng]);
      FoodMap._userMarker.setPopupContent(`<strong>${placeName}</strong><br><span style="font-size:0.8rem;color:#64748b;">(Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)})</span>`);
    } else {
      FoodMap._userMarker = L.circleMarker([lat, lng], {
        radius: 10,
        fillColor: '#2563eb',
        color: '#ffffff',
        weight: 3,
        opacity: 1,
        fillOpacity: 0.95
      }).addTo(map);
      FoodMap._userMarker.bindPopup(`<strong>${placeName}</strong><br><span style="font-size:0.8rem;color:#64748b;">(Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)})</span>`);
    }
    FoodMap._userMarker.openPopup();
    GeolocationManager.setStoredLocation(lat, lng, placeName, true);
  },

  // ──────────────────────────────────────────────────────────────
  // Universal Location Search Bar Autocomplete Helper
  // ──────────────────────────────────────────────────────────────
  _initMapSearchBar(map, inputId, resultsId, onSelect) {
    const input = document.getElementById(inputId);
    const resultsBox = document.getElementById(resultsId);
    if (!input || !resultsBox) return;

    let debounce = null;

    input.addEventListener('input', () => {
      const query = input.value.trim();
      clearTimeout(debounce);
      if (query.length < 2) {
        resultsBox.innerHTML = '';
        resultsBox.style.display = 'none';
        return;
      }

      // Display shimmer skeleton items immediately while fetching
      resultsBox.innerHTML = `
        <div class="skeleton-search-item">
          <div class="skeleton skeleton-title" style="width: 52%; height: 13px; margin-bottom: 4px;"></div>
          <div class="skeleton skeleton-text" style="width: 85%; height: 11px; margin-bottom: 0;"></div>
        </div>
        <div class="skeleton-search-item">
          <div class="skeleton skeleton-title" style="width: 64%; height: 13px; margin-bottom: 4px;"></div>
          <div class="skeleton skeleton-text" style="width: 72%; height: 11px; margin-bottom: 0;"></div>
        </div>
        <div class="skeleton-search-item">
          <div class="skeleton skeleton-title" style="width: 44%; height: 13px; margin-bottom: 4px;"></div>
          <div class="skeleton skeleton-text" style="width: 90%; height: 11px; margin-bottom: 0;"></div>
        </div>
      `;
      resultsBox.style.display = 'block';

      debounce = setTimeout(async () => {
        try {
          const resp = await fetch(`/api/locations/search/?q=${encodeURIComponent(query)}`);
          const data = await resp.json();
          resultsBox.innerHTML = '';

          if (!data.results || data.results.length === 0) {
            resultsBox.innerHTML = '<div class="map-search-item map-search-empty">No matching places found. Try a nearby town or district (e.g. Palandur, Bhandara, Nagpur).</div>';
            resultsBox.style.display = 'block';
            return;
          }

          data.results.forEach(place => {
            const item = document.createElement('div');
            item.className = 'map-search-item';
            const shortName = place.display_name.split(',')[0];
            item.innerHTML = `
              <div class="map-search-item-name">${shortName}</div>
              <div class="map-search-item-sub">${place.display_name}</div>
            `;
            item.addEventListener('click', () => {
              input.value = shortName;
              resultsBox.innerHTML = '';
              resultsBox.style.display = 'none';
              if (onSelect) {
                onSelect(place);
              }
            });
            resultsBox.appendChild(item);
          });

          resultsBox.style.display = 'block';
        } catch (err) {
          console.error('Map location search error:', err);
        }
      }, 300);
    });

    // Close results when clicking outside
    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !resultsBox.contains(e.target)) {
        resultsBox.style.display = 'none';
      }
    });

    // Keyboard navigation: Escape key closes results
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        resultsBox.style.display = 'none';
        input.blur();
      }
    });
  },

  // ──────────────────────────────────────────────────────────────
  // Location Picker (event_form page — drag pin on a small map)
  // ──────────────────────────────────────────────────────────────
  initLocationPicker(containerId, latInputId, lngInputId, addressInputId, searchInputId = 'pickerSearchInput') {
    if (!document.getElementById(containerId) || typeof L === 'undefined') return;

    const latInput = document.getElementById(latInputId);
    const lngInput = document.getElementById(lngInputId);

    // Initial coords: default to Palandur / central India if empty
    let initLat = parseFloat(latInput.value) || 20.9165;
    let initLng = parseFloat(lngInput.value) || 79.8592;
    let initZoom = (latInput.value && lngInput.value) ? 14 : 9;

    const map = L.map(containerId).setView([initLat, initLng], initZoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    // Dismiss map skeleton screen placeholder if present
    const pickerSkeleton = document.getElementById(containerId).querySelector('.skeleton-map-wrapper');
    if (pickerSkeleton) {
      setTimeout(() => {
        pickerSkeleton.classList.add('is-hidden');
        setTimeout(() => pickerSkeleton.remove(), 400);
      }, 300);
    }

    let marker = L.marker([initLat, initLng], { draggable: true }).addTo(map);

    function updateCoords(lat, lng) {
      latInput.value = lat.toFixed(7);
      lngInput.value = lng.toFixed(7);
    }

    if (latInput.value && lngInput.value) {
      updateCoords(initLat, initLng);
    }

    marker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      updateCoords(pos.lat, pos.lng);
    });

    map.on('click', (e) => {
      marker.setLatLng(e.latlng);
      updateCoords(e.latlng.lat, e.latlng.lng);
    });

    // Wire up location search bar for event submission form
    const searchInput = document.getElementById(searchInputId);
    const resultsBox = document.getElementById('pickerSearchResults');
    if (searchInput && resultsBox) {
      let debounce = null;
      searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        clearTimeout(debounce);
        if (query.length < 2) {
          resultsBox.innerHTML = '';
          resultsBox.style.display = 'none';
          return;
        }

        // Display skeleton placeholder search items
        resultsBox.innerHTML = `
          <div class="skeleton-search-item">
            <div class="skeleton skeleton-title" style="width: 50%; height: 13px; margin-bottom: 4px;"></div>
            <div class="skeleton skeleton-text" style="width: 82%; height: 11px; margin-bottom: 0;"></div>
          </div>
          <div class="skeleton-search-item">
            <div class="skeleton skeleton-title" style="width: 62%; height: 13px; margin-bottom: 4px;"></div>
            <div class="skeleton skeleton-text" style="width: 75%; height: 11px; margin-bottom: 0;"></div>
          </div>
        `;
        resultsBox.style.display = 'block';

        debounce = setTimeout(async () => {
          try {
            const resp = await fetch(`/api/locations/search/?q=${encodeURIComponent(query)}`);
            const data = await resp.json();
            resultsBox.innerHTML = '';

            if (!data.results || data.results.length === 0) {
              resultsBox.innerHTML = '<div class="map-search-item map-search-empty">No places found. Try another city or town name.</div>';
              resultsBox.style.display = 'block';
              return;
            }

            data.results.forEach(place => {
              const item = document.createElement('div');
              item.className = 'map-search-item';
              const shortName = place.display_name.split(',')[0];
              item.innerHTML = `
                <div class="map-search-item-name">${shortName}</div>
                <div class="map-search-item-sub">${place.display_name}</div>
              `;
              item.addEventListener('click', () => {
                searchInput.value = shortName;
                resultsBox.innerHTML = '';
                resultsBox.style.display = 'none';
                map.setView([place.lat, place.lon], 15);
                marker.setLatLng([place.lat, place.lon]);
                updateCoords(place.lat, place.lon);
                showToast(`Pin moved to: ${shortName}`, 'success');
              });
              resultsBox.appendChild(item);
            });
            resultsBox.style.display = 'block';
          } catch (err) {}
        }, 300);
      });

      document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
          resultsBox.style.display = 'none';
        }
      });
    }

    // Locate me button within picker
    const locateBtn = document.getElementById('btnPickerLocateMe');
    if (locateBtn) {
      locateBtn.addEventListener('click', (e) => {
        e.preventDefault();
        locateBtn.textContent = 'Detecting...';
        GeolocationManager.requestLocation(
          (coords) => {
            locateBtn.textContent = 'Use My Current Location';
            map.setView([coords.lat, coords.lng], 15);
            marker.setLatLng([coords.lat, coords.lng]);
            updateCoords(coords.lat, coords.lng);
            if (coords.isCoarse) {
              showToast(`Estimated network position near ${coords.locationName}. You can drag pin or search Palandur above.`, 'info');
            } else {
              showToast('Pin moved to your current location.', 'success');
            }
          },
          (err) => {
            locateBtn.textContent = 'Use My Current Location';
            showToast(err, 'error');
          }
        );
      });
    }
  }
};
