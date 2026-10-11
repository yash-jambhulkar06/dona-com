/**
 * Free Food Progressive Web App (PWA) Manager
 * - Handles Service Worker registration & background updates
 * - Completely prevents viewport zooming (pinch-to-zoom, double-tap zoom, gesture zoom)
 * - Enables native app behaviors (standalone mode, install banner, touch responsiveness)
 */

(function () {
  'use strict';

  let deferredInstallPrompt = null;

  // -------------------------------------------------------------------------
  // 1. Strict Zero-Zoom Enforcement (App Does Not Zoom)
  // -------------------------------------------------------------------------
  function enforceZeroZoom() {
    // A. Disable Safari iOS gesture zoom events
    document.addEventListener('gesturestart', function (e) {
      e.preventDefault();
    }, { passive: false });

    document.addEventListener('gesturechange', function (e) {
      e.preventDefault();
    }, { passive: false });

    document.addEventListener('gestureend', function (e) {
      e.preventDefault();
    }, { passive: false });

    // B. Disable multi-touch pinch zoom (allow map interactions on Leaflet)
    document.addEventListener('touchstart', function (e) {
      if (e.touches && e.touches.length > 1) {
        if (!e.target.closest('.leaflet-container')) {
          e.preventDefault();
        }
      }
    }, { passive: false });

    document.addEventListener('touchmove', function (e) {
      if (e.touches && e.touches.length > 1) {
        if (!e.target.closest('.leaflet-container')) {
          e.preventDefault();
        }
      }
    }, { passive: false });

    // C. Disable double-tap to zoom on mobile browsers
    let lastTouchTime = 0;
    document.addEventListener('touchend', function (e) {
      const now = Date.now();
      if (now - lastTouchTime <= 300) {
        const tag = (e.target.tagName || '').toUpperCase();
        // Allow taps inside text inputs and select boxes
        if (!['INPUT', 'TEXTAREA', 'SELECT', 'OPTION'].includes(tag) && !e.target.isContentEditable) {
          e.preventDefault();
        }
      }
      lastTouchTime = now;
    }, { passive: false });

    // D. Disable desktop / trackpad Ctrl + Wheel zoom
    document.addEventListener('wheel', function (e) {
      if (e.ctrlKey) {
        e.preventDefault();
      }
    }, { passive: false });

    // E. Disable keyboard zoom shortcuts (Ctrl/Cmd +, -, =)
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && ['+', '-', '=', '0'].includes(e.key)) {
        e.preventDefault();
      }
    });

    // F. Prevent callout menu on long press on app controls
    document.addEventListener('contextmenu', function (e) {
      if (e.target.closest('.btn, .brand-logo, .bottom-nav-item, .nav-link, .modal-sheet-handle, img')) {
        if (!e.target.closest('.user-selectable-text')) {
          e.preventDefault();
        }
      }
    });
  }

  // Activate zero zoom immediately
  enforceZeroZoom();

  // -------------------------------------------------------------------------
  // 2. Standalone Application Mode Detection
  // -------------------------------------------------------------------------
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches 
                    || window.matchMedia('(display-mode: fullscreen)').matches 
                    || window.navigator.standalone === true;

  if (isStandalone) {
    document.documentElement.classList.add('pwa-standalone');
    document.body?.classList.add('pwa-standalone');
    console.log('[PWA] Running in standalone native app mode');
  }

  // -------------------------------------------------------------------------
  // 3. Service Worker Registration & Seamless Updates
  // -------------------------------------------------------------------------
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js', { scope: '/' })
        .then((registration) => {
          console.log('[PWA] Service Worker registered with scope:', registration.scope);

          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  console.log('[PWA] New version ready for activation');
                  showUpdateBanner(newWorker);
                }
              });
            }
          });
        })
        .catch((err) => {
          console.warn('[PWA] Service Worker registration failed:', err);
        });

      // Reload when new worker takes over
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // 4. Native PWA Install Promotion
  // -------------------------------------------------------------------------
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;

    // Reveal install button in mobile drawer / profile if present
    const installBtns = document.querySelectorAll('.btn-pwa-install');
    installBtns.forEach((btn) => {
      btn.style.display = 'inline-flex';
    });

    // If not in standalone mode and user has not dismissed today, show the floating install HUD
    const dismissedTime = localStorage.getItem('ff_pwa_install_dismissed');
    const isDismissedRecently = dismissedTime && (Date.now() - parseInt(dismissedTime, 10) < 3 * 86400000);

    if (!isStandalone && !isDismissedRecently) {
      setTimeout(() => {
        showInstallFloatingBanner();
      }, 3500);
    }

    console.log('[PWA] Installation prompt captured');
  });

  // Global install trigger function
  window.triggerPwaInstall = async function () {
    if (!deferredInstallPrompt) {
      if (typeof showToast === 'function') {
        showToast('App is already installed or your browser supports installing via the browser menu (⋮ / Share -> Add to Home Screen).', 'info');
      }
      return;
    }

    deferredInstallPrompt.prompt();
    const choiceResult = await deferredInstallPrompt.userChoice;
    console.log(`[PWA] User choice: ${choiceResult.outcome}`);

    if (choiceResult.outcome === 'accepted') {
      console.log('[PWA] User accepted installation prompt');
      hideInstallBanner();
      const installBtns = document.querySelectorAll('.btn-pwa-install');
      installBtns.forEach((btn) => {
        btn.style.display = 'none';
      });
    }
    deferredInstallPrompt = null;
  };

  // Event fired after app is installed
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] Free Food successfully installed');
    deferredInstallPrompt = null;
    hideInstallBanner();
    const installBtns = document.querySelectorAll('.btn-pwa-install');
    installBtns.forEach((btn) => {
      btn.style.display = 'none';
    });

    if (typeof showToast === 'function') {
      showToast('Free Food has been installed to your Home Screen!', 'success');
    }
  });

  // -------------------------------------------------------------------------
  // 5. App Install Floating Banner Component
  // -------------------------------------------------------------------------
  function showInstallFloatingBanner() {
    if (document.getElementById('pwaInstallBanner') || isStandalone) return;

    const banner = document.createElement('div');
    banner.id = 'pwaInstallBanner';
    banner.className = 'pwa-install-hud';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Install App');

    banner.innerHTML = `
      <div class="pwa-install-hud-inner">
        <div class="pwa-install-app-icon">
          <img src="/static/images/icons/icon-192.png" alt="Free Food Icon" width="44" height="44">
        </div>
        <div class="pwa-install-text">
          <div class="pwa-install-title">Install Free Food App</div>
          <div class="pwa-install-desc">Fast 1-tap access, offline view & live food alerts</div>
        </div>
        <div class="pwa-install-actions">
          <button type="button" class="pwa-btn-install" id="btnPwaHudInstall">Install</button>
          <button type="button" class="pwa-btn-close" id="btnPwaHudDismiss" aria-label="Dismiss">&times;</button>
        </div>
      </div>
    `;

    document.body.appendChild(banner);

    document.getElementById('btnPwaHudInstall')?.addEventListener('click', () => {
      window.triggerPwaInstall();
    });

    document.getElementById('btnPwaHudDismiss')?.addEventListener('click', () => {
      hideInstallBanner();
      localStorage.setItem('ff_pwa_install_dismissed', Date.now().toString());
    });
  }

  function hideInstallBanner() {
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) {
      banner.classList.add('pwa-hud-closing');
      setTimeout(() => banner.remove(), 250);
    }
  }

  // -------------------------------------------------------------------------
  // 6. Online / Offline Connectivity Notifications
  // -------------------------------------------------------------------------
  window.addEventListener('offline', () => {
    if (typeof showToast === 'function') {
      showToast('You are currently offline. Showing cached listings.', 'warning');
    }
  });

  window.addEventListener('online', () => {
    if (typeof showToast === 'function') {
      showToast('Internet connection restored. Live events updated.', 'success');
    }
  });

  // -------------------------------------------------------------------------
  // 7. Update Notification Banner Helper
  // -------------------------------------------------------------------------
  function showUpdateBanner(worker) {
    if (document.getElementById('pwaUpdateBanner')) return;

    const banner = document.createElement('div');
    banner.id = 'pwaUpdateBanner';
    banner.className = 'pwa-update-hud';

    banner.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.6rem;">
        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #22c55e;"></span>
        <span>A new update of Free Food is ready.</span>
      </div>
      <button type="button" id="btnPwaUpdateApply" class="btn btn-primary btn-sm" style="padding: 0.35rem 0.8rem; font-size: 0.8rem;">
        Update
      </button>
    `;

    document.body.appendChild(banner);

    document.getElementById('btnPwaUpdateApply')?.addEventListener('click', () => {
      worker.postMessage({ type: 'SKIP_WAITING' });
      banner.remove();
    });

    setTimeout(() => {
      banner.remove();
    }, 12000);
  }
})();
