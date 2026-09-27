/**
 * Main application JavaScript
 * Dona.Com — Community Free-Food Discovery Platform
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile hamburger menu toggle & drawer handler
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const mobileDrawer = document.getElementById('mobileMenuDrawer');
  const mobileBackdrop = document.getElementById('mobileMenuBackdrop');

  function openMobileMenu() {
    if (!mobileBtn || !mobileDrawer) return;
    mobileBtn.classList.add('is-active');
    mobileBtn.setAttribute('aria-expanded', 'true');
    mobileDrawer.classList.add('is-open');
    mobileDrawer.setAttribute('aria-hidden', 'false');
    if (mobileBackdrop) mobileBackdrop.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileMenu() {
    if (!mobileBtn || !mobileDrawer) return;
    mobileBtn.classList.remove('is-active');
    mobileBtn.setAttribute('aria-expanded', 'false');
    mobileDrawer.classList.remove('is-open');
    mobileDrawer.setAttribute('aria-hidden', 'true');
    if (mobileBackdrop) mobileBackdrop.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  if (mobileBtn && mobileDrawer) {
    mobileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = mobileBtn.classList.contains('is-active');
      if (isOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });

    if (mobileBackdrop) {
      mobileBackdrop.addEventListener('click', closeMobileMenu);
    }

    // Close when clicking any nav link inside drawer
    mobileDrawer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileDrawer.classList.contains('is-open')) {
        closeMobileMenu();
      }
    });

    // Close if window resized to desktop viewport
    window.addEventListener('resize', () => {
      if (window.innerWidth > 992 && mobileDrawer.classList.contains('is-open')) {
        closeMobileMenu();
      }
    });
  }

  // Dismissible alerts
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // Favorite toggle AJAX handler
  document.querySelectorAll('.fav-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const eventId = btn.dataset.eventId;
      if (!eventId) return;

      const csrfToken = getCookie('csrftoken');
      if (!csrfToken) {
        window.location.href = '/login/';
        return;
      }

      try {
        const response = await fetch(`/food/${eventId}/favorite/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          }
        });

        if (response.status === 403 || response.status === 401 || response.redirected) {
          window.location.href = '/login/';
          return;
        }

        const data = await response.json();
        if (data.status === 'success') {
          btn.classList.toggle('is-favorited', data.favorited);
          btn.textContent = data.favorited ? 'Saved' : 'Save';
          showToast(data.message, 'success');
        } else {
          showToast(data.message || 'Error updating favorite', 'error');
        }
      } catch (err) {
        console.error('Favorite error:', err);
      }
    });
  });

  // Share verified event pages with native share or a clipboard fallback.
  document.querySelectorAll('.share-event-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const shareData = {
        title: btn.dataset.shareTitle || document.title,
        text: btn.dataset.shareText || document.title,
        url: window.location.href
      };

      try {
        if (navigator.share) {
          await navigator.share(shareData);
          return;
        }

        await copyTextToClipboard(shareData.url);
        showToast('Event link copied. Share it with someone who needs it.', 'success');
      } catch (err) {
        if (err && err.name !== 'AbortError') {
          showToast('Unable to share this event right now.', 'error');
        }
      }
    });
  });
});

async function copyTextToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.setAttribute('readonly', '');
  textArea.style.position = 'fixed';
  textArea.style.opacity = '0';
  document.body.appendChild(textArea);
  textArea.select();
  const copied = document.execCommand('copy');
  textArea.remove();
  if (!copied) throw new Error('Clipboard copy failed');
}

/**
 * Gets a cookie value by name (e.g. csrftoken)
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Lightweight Toast Notification (Red Theme)
 */
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: calc(var(--bottom-nav-height, 64px) + 16px);
      right: 1.25rem;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: min(400px, calc(100vw - 2.5rem));
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? '#16a34a' : (type === 'error' ? '#dc2626' : '#111827');
  toast.style.cssText = `
    background: ${bg};
    color: #ffffff;
    padding: 0.75rem 1.15rem;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
    animation: fadeIn 0.25s ease;
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  `;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(4px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 260);
  }, 3500);
}

/**
 * Modal helpers
 */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('is-active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('is-active');
}
