/**
 * Free Food Progressive Web App (PWA) Manager
 * Handles Service Worker registration, updates, installation prompt, and online/offline status.
 */

(function () {
  'use strict';

  let deferredInstallPrompt = null;

  // 1. Detect Standalone PWA Mode
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  if (isStandalone) {
    document.documentElement.classList.add('pwa-standalone');
    console.log('[PWA] Running in standalone application mode');
  }

  // 2. Service Worker Registration & Safe Updates
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js', { scope: '/' })
        .then((registration) => {
          console.log('[PWA] Service Worker registered with scope:', registration.scope);

          // Check if an update is found
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // A new version has been installed and is waiting
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

      // Handle controller change (service worker activated after update)
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    });
  }

  // 3. Native PWA Installation Capture
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the default browser mini-infobar from appearing on mobile
    e.preventDefault();
    deferredInstallPrompt = e;

    // Reveal install button in mobile drawer / profile if available
    const installBtns = document.querySelectorAll('.btn-pwa-install');
    installBtns.forEach((btn) => {
      btn.style.display = 'inline-flex';
    });

    console.log('[PWA] Installation prompt captured and available');
  });

  // Global trigger function to prompt installation
  window.triggerPwaInstall = async function () {
    if (!deferredInstallPrompt) {
      if (typeof showToast === 'function') {
        showToast('App is already installed or your browser handles installation from the menu.', 'info');
      }
      return;
    }

    deferredInstallPrompt.prompt();
    const choiceResult = await deferredInstallPrompt.userChoice;
    console.log(`[PWA] User choice: ${choiceResult.outcome}`);

    if (choiceResult.outcome === 'accepted') {
      console.log('[PWA] User accepted installation prompt');
      const installBtns = document.querySelectorAll('.btn-pwa-install');
      installBtns.forEach((btn) => {
        btn.style.display = 'none';
      });
    }
    deferredInstallPrompt = null;
  };

  // Event fired after app is successfully installed
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] Free Food successfully installed as an app');
    deferredInstallPrompt = null;
    const installBtns = document.querySelectorAll('.btn-pwa-install');
    installBtns.forEach((btn) => {
      btn.style.display = 'none';
    });

    if (typeof showToast === 'function') {
      showToast('Free Food has been added to your Home Screen!', 'success');
    }
  });

  // 4. Online / Offline Connectivity Notifications
  window.addEventListener('offline', () => {
    if (typeof showToast === 'function') {
      showToast('You are currently offline. Showing cached content.', 'warning');
    }
  });

  window.addEventListener('online', () => {
    if (typeof showToast === 'function') {
      showToast('Internet connection restored. Live events updated.', 'success');
    }
  });

  // 5. Update Banner Helper (Non-intrusive)
  function showUpdateBanner(worker) {
    if (document.getElementById('pwaUpdateBanner')) return;

    const banner = document.createElement('div');
    banner.id = 'pwaUpdateBanner';
    banner.style.cssText = `
      position: fixed;
      bottom: calc(var(--bottom-nav-height, 64px) + 16px);
      left: 1rem;
      right: 1rem;
      max-width: 440px;
      margin: 0 auto;
      background: #111827;
      color: #ffffff;
      padding: 0.85rem 1.15rem;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
      z-index: 1080;
      font-size: 0.875rem;
      animation: toastSlideUp 0.3s ease;
    `;

    banner.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.6rem;">
        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #22c55e;"></span>
        <span>A new update of Free Food is available.</span>
      </div>
      <button type="button" id="btnPwaUpdateApply" style="background: #dc2626; color: #ffffff; border: none; padding: 0.35rem 0.75rem; border-radius: 8px; font-weight: 700; font-size: 0.8rem; cursor: pointer;">
        Update
      </button>
    `;

    document.body.appendChild(banner);

    document.getElementById('btnPwaUpdateApply')?.addEventListener('click', () => {
      worker.postMessage({ type: 'SKIP_WAITING' });
      banner.remove();
    });

    // Auto dismiss after 10 seconds if not clicked
    setTimeout(() => {
      banner.remove();
    }, 10000);
  }
})();
