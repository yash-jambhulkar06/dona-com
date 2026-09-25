/**
 * Map Integration using Leaflet + OpenStreetMap
 * Dona.Com — Community Free-Food Discovery Platform
 * Red Theme (Emoji-Free)
 */

const FoodMap = {
  initFullMap(containerId, pins) {
    if (!document.getElementById(containerId) || typeof L === 'undefined') return null;

    // Default center: India center or first pin
    let center = [21.1458, 79.0882];
    let zoom = 5;

    if (pins && pins.length > 0) {
      center = [pins[0].lat, pins[0].lng];
      zoom = pins.length === 1 ? 14 : 11;
    }

    const map = L.map(containerId).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    const bounds = [];

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

    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }

    // Try to plot user location if stored
    const userLoc = GeolocationManager.getStoredLocation();
    if (userLoc) {
      const userIcon = L.circleMarker([userLoc.lat, userLoc.lng], {
        radius: 8,
        fillColor: '#dc2626',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      }).addTo(map);
      userIcon.bindPopup('<strong>Your detected location</strong>');
    }

    return map;
  },

  initLocationPicker(containerId, latInputId, lngInputId, addressInputId) {
    if (!document.getElementById(containerId) || typeof L === 'undefined') return;

    const latInput = document.getElementById(latInputId);
    const lngInput = document.getElementById(lngInputId);

    // Initial coords (default or existing values)
    let initLat = parseFloat(latInput.value) || 21.1458;
    let initLng = parseFloat(lngInput.value) || 79.0882;
    let initZoom = (latInput.value && lngInput.value) ? 14 : 5;

    const map = L.map(containerId).setView([initLat, initLng], initZoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

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

    // Locate me button within picker
    const locateBtn = document.getElementById('btnPickerLocateMe');
    if (locateBtn) {
      locateBtn.addEventListener('click', (e) => {
        e.preventDefault();
        GeolocationManager.requestLocation(
          (coords) => {
            map.setView([coords.lat, coords.lng], 15);
            marker.setLatLng([coords.lat, coords.lng]);
            updateCoords(coords.lat, coords.lng);
            showToast('Pin moved to your current location.', 'success');
          },
          (err) => {
            showToast(err, 'error');
          }
        );
      });
    }
  }
};
