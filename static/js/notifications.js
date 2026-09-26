/**
 * Real-Time Mobile-App Style Notifications
 * Dona.Com — Community Free-Food Discovery Platform
 */

(function () {
  'use strict';

  // State
  let lastServerTime = null;
  let pollIntervalId = null;
  let isPollingActive = true;
  let activeHudTimer = null;
  let soundEnabled = localStorage.getItem('dona_notif_sound') !== 'false';
  let knownIds = new Set();
  let currentFilter = 'all'; // 'all' or 'unread'
  let cachedNotifications = [];
  let isFirstLoad = true;

  // DOM Elements
  let bellBtn = null;
  let badgeEl = null;
  let dropdownEl = null;
  let backdropEl = null;
  let listContainerEl = null;
  let unreadPillEl = null;
  let hudEl = null;

  // Initialize once DOM is ready (Only for logged-in members)
  document.addEventListener('DOMContentLoaded', () => {
    const isUserAuth = document.body.dataset.userAuthenticated === 'true';
    if (!isUserAuth) {
      return; // Strictly disabled for visitors who are not logged in
    }

    initElements();
    setupEventListeners();
    requestNotificationPermissionIfAppropriate();
    
    // Initial fetch to load notifications and badge
    fetchNotifications(true);

    // Start Real-Time Polling (every 4.5 seconds)
    startPolling();
  });


  function initElements() {
    bellBtn = document.getElementById('notificationBellBtn');
    badgeEl = document.getElementById('notificationBadge');
    dropdownEl = document.getElementById('notificationDropdown');
    backdropEl = document.getElementById('notificationSheetBackdrop');
    listContainerEl = document.getElementById('notifTrayBody');
    unreadPillEl = document.getElementById('notifUnreadCountPill');
    hudEl = document.getElementById('mobilePushHud');
  }

  function setupEventListeners() {
    // Toggle notification tray on bell click
    if (bellBtn) {
      bellBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleTray();
      });
    }

    // Close when clicking mobile backdrop
    if (backdropEl) {
      backdropEl.addEventListener('click', closeTray);
    }

    // Close desktop dropdown on click outside
    document.addEventListener('click', (e) => {
      if (dropdownEl && dropdownEl.classList.contains('is-open')) {
        if (!dropdownEl.contains(e.target) && (!bellBtn || !bellBtn.contains(e.target))) {
          closeTray();
        }
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeTray();
        dismissHud();
      }
    });

    // Tabs: All vs Unread
    const tabAll = document.getElementById('notifTabAll');
    const tabUnread = document.getElementById('notifTabUnread');

    if (tabAll && tabUnread) {
      tabAll.addEventListener('click', () => switchTab('all'));
      tabUnread.addEventListener('click', () => switchTab('unread'));
    }

    // Mark all as read button
    const markAllBtn = document.getElementById('notifMarkAllBtn');
    if (markAllBtn) {
      markAllBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        markAllAsRead();
      });
    }

    // Sound toggle button
    const soundToggleBtn = document.getElementById('notifSoundToggleBtn');
    if (soundToggleBtn) {
      updateSoundIcon(soundToggleBtn);
      soundToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        soundEnabled = !soundEnabled;
        localStorage.setItem('dona_notif_sound', soundEnabled ? 'true' : 'false');
        updateSoundIcon(soundToggleBtn);
        if (soundEnabled) {
          playMobileChime();
        }
      });
    }

    // Clear All Button
    const clearAllBtn = document.getElementById('notifClearAllBtn');
    if (clearAllBtn) {
      clearAllBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearAllNotifications();
      });
    }

    // HUD banner swipe-up gesture on mobile
    if (hudEl) {
      let touchStartY = 0;
      hudEl.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
      }, { passive: true });

      hudEl.addEventListener('touchend', (e) => {
        const touchEndY = e.changedTouches[0].clientY;
        if (touchStartY - touchEndY > 30) {
          // Swiped up!
          dismissHud();
        }
      }, { passive: true });
    }

    // Adaptive Tab Visibility: Poll fast when active, slow when hidden
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Slow down to 15s in background
        resetPolling(15000);
      } else {
        // Immediately fetch and speed back up to 4.5s
        fetchNotifications(false);
        resetPolling(4500);
      }
    });
  }

  function startPolling() {
    if (pollIntervalId) clearInterval(pollIntervalId);
    pollIntervalId = setInterval(() => {
      if (isPollingActive) {
        fetchNotifications(false);
      }
    }, 4500);
  }

  function resetPolling(intervalMs) {
    if (pollIntervalId) clearInterval(pollIntervalId);
    pollIntervalId = setInterval(() => {
      if (isPollingActive) {
        fetchNotifications(false);
      }
    }, intervalMs);
  }

  /**
   * Fetches latest notifications from API
   */
  async function fetchNotifications(initial = false) {
    try {
      let url = '/notifications/api/list/?limit=25';
      const response = await fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) return;

      const data = await response.json();
      if (data.status === 'success') {
        const notifications = data.notifications || [];
        const unreadCount = data.unread_count || 0;

        // Check for NEW notifications since last poll
        if (!initial && !isFirstLoad) {
          const brandNewItems = notifications.filter(n => !knownIds.has(n.id) && !n.is_read);
          if (brandNewItems.length > 0) {
            // Trigger Mobile-App Real-Time Alert for the newest item!
            const newest = brandNewItems[0];
            showMobilePushHud(newest);
            playMobileChime();
            triggerMobileVibration();
            triggerNativeBrowserNotification(newest);
            triggerBellRingAnimation();
          }
        }

        // Cache known IDs
        notifications.forEach(n => knownIds.add(n.id));

        cachedNotifications = notifications;
        lastServerTime = data.server_time;
        isFirstLoad = false;

        // Update UI
        updateBadge(unreadCount);
        renderNotificationsList();
      }
    } catch (err) {
      console.warn('Real-time notifications poll error:', err);
    }
  }

  /**
   * Updates unread badge with pulse animation
   */
  function updateBadge(count) {
    if (!badgeEl) return;
    if (count > 0) {
      badgeEl.textContent = count > 99 ? '99+' : count;
      badgeEl.style.display = 'flex';
      badgeEl.classList.add('pulse');
    } else {
      badgeEl.style.display = 'none';
      badgeEl.classList.remove('pulse');
    }

    if (unreadPillEl) {
      unreadPillEl.textContent = count > 0 ? `${count} new` : '0';
    }
  }

  /**
   * Shakes the bell icon
   */
  function triggerBellRingAnimation() {
    if (!bellBtn) return;
    bellBtn.classList.remove('bell-ring-active');
    void bellBtn.offsetWidth; // trigger reflow
    bellBtn.classList.add('bell-ring-active');
    setTimeout(() => {
      bellBtn.classList.remove('bell-ring-active');
    }, 1000);
  }

  /**
   * Renders skeleton shimmer placeholders while notifications are loading
   */
  function renderNotificationsSkeleton() {
    if (!listContainerEl) return;
    listContainerEl.innerHTML = `
      <div class="skeleton-notif-item">
        <div class="skeleton skeleton-icon"></div>
        <div class="skeleton-notif-content">
          <div class="skeleton skeleton-title" style="width: 58%; height: 14px;"></div>
          <div class="skeleton skeleton-text" style="width: 90%;"></div>
          <div class="skeleton skeleton-text short" style="width: 35%; height: 10px;"></div>
        </div>
      </div>
      <div class="skeleton-notif-item">
        <div class="skeleton skeleton-icon"></div>
        <div class="skeleton-notif-content">
          <div class="skeleton skeleton-title" style="width: 65%; height: 14px;"></div>
          <div class="skeleton skeleton-text" style="width: 82%;"></div>
          <div class="skeleton skeleton-text short" style="width: 40%; height: 10px;"></div>
        </div>
      </div>
      <div class="skeleton-notif-item">
        <div class="skeleton skeleton-icon"></div>
        <div class="skeleton-notif-content">
          <div class="skeleton skeleton-title" style="width: 50%; height: 14px;"></div>
          <div class="skeleton skeleton-text" style="width: 86%;"></div>
          <div class="skeleton skeleton-text short" style="width: 30%; height: 10px;"></div>
        </div>
      </div>
    `;
  }

  /**
   * Renders the notifications inside the dropdown / bottom-sheet
   */
  function renderNotificationsList() {
    if (!listContainerEl) return;

    let items = cachedNotifications;
    if (currentFilter === 'unread') {
      items = items.filter(n => !n.is_read);
    }

    if (items.length === 0) {
      const msg = currentFilter === 'unread' ? "You're all caught up! No unread notifications." : "No notifications right now.";
      listContainerEl.innerHTML = `
        <div class="notif-empty-state">
          <div class="notif-empty-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </div>
          <div class="notif-empty-title">All Caught Up</div>
          <p class="notif-empty-desc">${msg}</p>
        </div>
      `;
      return;
    }

    const html = items.map(item => {
      const iconData = getIconForType(item.type);
      const isUnread = !item.is_read;
      return `
        <div class="notif-item ${isUnread ? 'is-unread' : ''}" data-id="${item.id}" data-url="${escapeHtml(item.target_url)}">
          <div class="notif-item-icon ${iconData.cssClass}">
            ${iconData.svg}
          </div>
          <div class="notif-item-text">
            <div class="notif-item-title">${escapeHtml(item.title)}</div>
            <div class="notif-item-msg">${escapeHtml(item.message)}</div>
            <div class="notif-item-footer">
              <span class="notif-item-time">${escapeHtml(item.time_ago)}</span>
              ${isUnread ? '<span class="notif-unread-dot" title="Unread"></span>' : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');

    listContainerEl.innerHTML = html;

    // Attach click listeners to notification items
    listContainerEl.querySelectorAll('.notif-item').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const id = el.dataset.id;
        const targetUrl = el.dataset.url;
        handleNotificationClick(id, targetUrl);
      });
    });
  }

  function switchTab(filter) {
    currentFilter = filter;
    const tabAll = document.getElementById('notifTabAll');
    const tabUnread = document.getElementById('notifTabUnread');

    if (filter === 'all') {
      tabAll.classList.add('active');
      tabUnread.classList.remove('active');
    } else {
      tabUnread.classList.add('active');
      tabAll.classList.remove('active');
    }

    renderNotificationsList();
  }

  /**
   * Opens / Closes the tray (Dropdown on Desktop, Bottom Sheet on Mobile)
   */
  function toggleTray() {
    if (!dropdownEl) return;
    const isOpen = dropdownEl.classList.contains('is-open');
    if (isOpen) {
      closeTray();
    } else {
      openTray();
    }
  }

  function openTray() {
    if (!dropdownEl) return;
    dropdownEl.classList.add('is-open');
    if (bellBtn) bellBtn.setAttribute('aria-expanded', 'true');

    if (isFirstLoad && (!cachedNotifications || cachedNotifications.length === 0)) {
      renderNotificationsSkeleton();
    }

    // Close mobile hamburger menu drawer if open
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileDrawer = document.getElementById('mobileMenuDrawer');
    const mobileBackdrop = document.getElementById('mobileMenuBackdrop');
    if (mobileBtn && mobileDrawer && mobileDrawer.classList.contains('is-open')) {
      mobileBtn.classList.remove('is-active');
      mobileBtn.setAttribute('aria-expanded', 'false');
      mobileDrawer.classList.remove('is-open');
      mobileDrawer.setAttribute('aria-hidden', 'true');
      if (mobileBackdrop) mobileBackdrop.classList.remove('is-open');
    }

    // On mobile / tablet screens (<= 992px), activate backdrop and lock body scroll
    if (window.innerWidth <= 992) {
      if (backdropEl) backdropEl.classList.add('is-active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeTray() {
    if (!dropdownEl) return;
    dropdownEl.classList.remove('is-open');
    if (bellBtn) bellBtn.setAttribute('aria-expanded', 'false');
    if (backdropEl) backdropEl.classList.remove('is-active');
    document.body.style.overflow = '';
  }

  /**
   * Handles user tapping on a notification
   */
  async function handleNotificationClick(id, targetUrl) {
    // Optimistically mark as read locally
    const item = cachedNotifications.find(n => n.id === id);
    if (item) item.is_read = true;
    renderNotificationsList();
    closeTray();

    // Call API in background
    try {
      const csrf = getCsrfToken();
      await fetch(`/notifications/api/read/${id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf,
          'Content-Type': 'application/json'
        }
      });
      // Re-fetch badge count
      const countRes = await fetch('/notifications/api/unread-count/');
      if (countRes.ok) {
        const countData = await countRes.json();
        updateBadge(countData.unread_count);
      }
    } catch (e) {
      console.warn('Error marking notification read:', e);
    }

    // Navigate to target
    if (targetUrl && targetUrl !== '#') {
      window.location.href = targetUrl;
    }
  }

  /**
   * Mark all as read
   */
  async function markAllAsRead() {
    try {
      const csrf = getCsrfToken();
      const response = await fetch('/notifications/api/read-all/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        cachedNotifications.forEach(n => n.is_read = true);
        updateBadge(0);
        renderNotificationsList();
      }
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  }

  /**
   * Clears all notifications
   */
  async function clearAllNotifications() {
    try {
      const csrf = getCsrfToken();
      const res = await fetch('/notifications/api/clear-all/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf || '',
          'Content-Type': 'application/json'
        }
      });

      if (res.ok) {
        cachedNotifications = [];
        knownIds.clear();
        updateBadge(0);
        renderNotificationsList();
        if (typeof showToast === 'function') {
          showToast('All notifications cleared', 'info');
        }
      }
    } catch (err) {
      console.error('Error clearing notifications:', err);
    }
  }

  /**
   * Floating Mobile Push HUD Banner
   */
  function showMobilePushHud(item) {
    if (!hudEl) {
      createMobilePushHudElement();
    }

    if (activeHudTimer) {
      clearTimeout(activeHudTimer);
      activeHudTimer = null;
    }

    const titleEl = document.getElementById('hudTitle');
    const msgEl = document.getElementById('hudMessage');
    const timeEl = document.getElementById('hudTime');
    const viewBtn = document.getElementById('hudViewBtn');
    const progressBar = document.getElementById('hudProgressBarFill');

    if (titleEl) titleEl.textContent = item.title;
    if (msgEl) msgEl.textContent = item.message;
    if (timeEl) timeEl.textContent = item.time_ago || 'Just now';

    if (viewBtn) {
      viewBtn.href = item.target_url || '/food/';
      viewBtn.onclick = (e) => {
        e.stopPropagation();
        handleNotificationClick(item.id, item.target_url);
        dismissHud();
      };
    }

    // Clicking the entire HUD opens it
    hudEl.onclick = () => {
      handleNotificationClick(item.id, item.target_url);
      dismissHud();
    };

    // Close button
    const closeBtn = document.getElementById('hudCloseBtn');
    if (closeBtn) {
      closeBtn.onclick = (e) => {
        e.stopPropagation();
        dismissHud();
      };
    }

    // Reset and start animation
    hudEl.classList.remove('is-dismissing');
    hudEl.classList.add('is-visible');

    if (progressBar) {
      progressBar.style.transition = 'none';
      progressBar.style.width = '100%';
      setTimeout(() => {
        progressBar.style.transition = 'width 5.5s linear';
        progressBar.style.width = '0%';
      }, 50);
    }

    // Auto dismiss after 5.5 seconds
    activeHudTimer = setTimeout(() => {
      dismissHud();
    }, 5500);
  }

  function dismissHud() {
    if (!hudEl) return;
    hudEl.classList.add('is-dismissing');
    setTimeout(() => {
      hudEl.classList.remove('is-visible', 'is-dismissing');
    }, 400);
  }

  function createMobilePushHudElement() {
    const div = document.createElement('div');
    div.id = 'mobilePushHud';
    div.className = 'mobile-push-hud';
    div.innerHTML = `
      <div class="hud-inner">
        <div class="hud-app-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
        </div>
        <div class="hud-content">
          <div class="hud-header">
            <span class="hud-brand">
              <span>Dona.Com</span>
              <span>•</span>
              <span id="hudTime">Just now</span>
            </span>
            <button type="button" class="hud-action-dismiss" id="hudCloseBtn" aria-label="Dismiss">&times;</button>
          </div>
          <div class="hud-title" id="hudTitle">Free Food Notification</div>
          <div class="hud-message" id="hudMessage">New update available</div>
          <div class="hud-actions">
            <a href="#" class="hud-action-view" id="hudViewBtn">View Details &rarr;</a>
          </div>
        </div>
      </div>
      <div class="hud-progress-bar">
        <div class="hud-progress-fill" id="hudProgressBarFill"></div>
      </div>
    `;
    document.body.appendChild(div);
    hudEl = div;
  }

  /**
   * Pure Web Audio API Sound Synthesizer
   * Creates an authentic iOS / Android mobile chime ding.
   * Zero external mp3 dependencies, 100% reliable across all browsers.
   */
  function playMobileChime() {
    if (!soundEnabled) return;

    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;

      const ctx = new AudioContext();
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      const now = ctx.currentTime;

      // Note 1: 587.33 Hz (D5)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now);
      gain1.gain.setValueAtTime(0, now);
      gain1.gain.linearRampToValueAtTime(0.25, now + 0.02);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.35);

      // Note 2: 880.00 Hz (A5 - pleasant chime harmony)
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(880.00, now + 0.12);
      gain2.gain.setValueAtTime(0, now + 0.12);
      gain2.gain.linearRampToValueAtTime(0.35, now + 0.15);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.7);

      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.12);
      osc2.stop(now + 0.7);

    } catch (e) {
      // AudioContext might be blocked by autoplay policies until user gesture
    }
  }

  /**
   * Mobile Device Physical Vibration
   */
  function triggerMobileVibration() {
    if ('vibrate' in navigator) {
      try {
        navigator.vibrate([80, 50, 80]);
      } catch (e) {}
    }
  }

  /**
   * Native OS / Browser Notification API
   */
  function requestNotificationPermissionIfAppropriate() {
    if ('Notification' in window && Notification.permission === 'default') {
      // We can gently request after user interacts
    }
  }

  function triggerNativeBrowserNotification(item) {
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        const notif = new Notification(item.title, {
          body: item.message,
          icon: '/static/img/favicon.png',
          badge: '/static/img/favicon.png',
          tag: item.id
        });
        notif.onclick = () => {
          window.focus();
          handleNotificationClick(item.id, item.target_url);
        };
      } catch (e) {}
    }
  }

  /**
   * Helper Icons for Categories
   */
  function getIconForType(type) {
    switch (type) {
      case 'EVENT_APPROVED':
        return {
          cssClass: 'notif-icon-approved',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`
        };
      case 'EVENT_REJECTED':
        return {
          cssClass: 'notif-icon-rejected',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`
        };
      case 'NEW_SUBMISSION':
        return {
          cssClass: 'notif-icon-submission',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>`
        };
      case 'NEW_REPORT':
      case 'REPORT_RESOLVED':
        return {
          cssClass: 'notif-icon-report',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>`
        };
      case 'EVENT_NEARBY':
      case 'EVENT_LIVE':
        return {
          cssClass: 'notif-icon-food',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"></path><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path><line x1="6" y1="1" x2="6" y2="4"></line><line x1="10" y1="1" x2="10" y2="4"></line><line x1="14" y1="1" x2="14" y2="4"></line></svg>`
        };
      default:
        return {
          cssClass: 'notif-icon-system',
          svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
        };
    }
  }

  function updateSoundIcon(btn) {
    if (!btn) return;
    if (soundEnabled) {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;
      btn.title = "Mute notification sound";
      btn.classList.add('active');
    } else {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`;
      btn.title = "Unmute notification sound";
      btn.classList.remove('active');
    }
  }

  function getCsrfToken() {
    let token = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === 'csrftoken=') {
          token = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return token;
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }

  /**
   * Browser Push Notifications (Web Notification API) & 5 km Proximity Alerts (Future Scope Item 3)
   */
  function requestNotificationPermissionIfAppropriate() {
    setupProximityPush();
  }

  function setupProximityPush() {
    const btn = document.getElementById('btnEnableProximityAlerts');
    if (!btn) return;

    if (!('Notification' in window)) {
      btn.style.display = 'none';
      return;
    }

    if (Notification.permission === 'granted') {
      btn.textContent = 'Alerts Active (5 km)';
      btn.style.background = '#059669';
      btn.style.color = '#ffffff';
    }

    btn.addEventListener('click', async () => {
      try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          btn.textContent = 'Locating...';
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              async (position) => {
                await registerProximityCoordinates(position.coords.latitude, position.coords.longitude);
                btn.textContent = 'Alerts Active (5 km)';
                btn.style.background = '#059669';
                btn.style.color = '#ffffff';
                triggerNativeBrowserNotification({
                  id: 'welcome-alert',
                  title: 'Dona.Com Proximity Alerts Active',
                  message: 'You will receive browser notifications whenever free food is published within 5 km of your location.',
                  target_url: '/food/'
                });
              },
              (err) => {
                btn.textContent = 'Alerts Enabled';
                btn.style.background = '#059669';
              }
            );
          }
        } else {
          btn.textContent = 'Alerts Blocked';
          btn.style.background = '#64748b';
        }
      } catch (e) {
        console.error('Proximity alert setup error:', e);
      }
    });
  }

  async function registerProximityCoordinates(lat, lng) {
    try {
      await fetch('/notifications/api/register-proximity/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          latitude: lat,
          longitude: lng,
          radius_km: 5.0
        })
      });
    } catch (e) {
      console.warn('Could not register proximity coordinates:', e);
    }
  }

  function triggerNativeBrowserNotification(notif) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return;
    }
    try {
      const nativeNotif = new Notification(notif.title, {
        body: notif.message,
        icon: '/static/icons/dona-icon.png',
        tag: `dona-notif-${notif.id}`,
        data: { url: notif.target_url }
      });
      nativeNotif.onclick = function () {
        window.focus();
        if (notif.target_url && notif.target_url !== '/') {
          window.location.href = notif.target_url;
        }
      };
    } catch (e) {
      console.warn('Native notification display error:', e);
    }
  }

  // Expose global clear trigger
  window.donaClearAllNotifications = clearAllNotifications;

})();
