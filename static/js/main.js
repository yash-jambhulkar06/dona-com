/**
 * Main application JavaScript
 * Free Food — Community Free-Food Discovery Platform
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

  // Favorite toggle AJAX handler with immediate visual feedback & heart pop animation
  document.querySelectorAll('.fav-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const eventId = btn.dataset.eventId;
      if (!eventId) return;

      const csrfToken = getCookie('csrftoken');
      if (!csrfToken) {
        if (window.InteractionFeedback) window.InteractionFeedback.startTopProgress();
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
        return;
      }

      // Prevent repeated clicks during processing
      btn.style.pointerEvents = 'none';
      btn.style.opacity = '0.75';
      const labelSpan = btn.querySelector('.fav-btn-label, .fav-text');
      const origText = labelSpan ? labelSpan.textContent : (btn.querySelector('svg') ? null : btn.textContent);
      if (labelSpan) {
        labelSpan.textContent = 'Saving...';
      }

      try {
        const response = await fetch(`/food/${eventId}/favorite/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.status === 403 || response.status === 401 || response.redirected) {
          if (window.InteractionFeedback) window.InteractionFeedback.startTopProgress();
          window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
          return;
        }

        const data = await response.json();
        if (data.status === 'success') {
          btn.classList.toggle('is-favorited', data.favorited);
          btn.classList.remove('is-pop');
          void btn.offsetWidth; // Force reflow to retrigger animation
          btn.classList.add('is-pop');

          // Update text label: Save / Saved
          if (labelSpan) {
            labelSpan.textContent = data.favorited ? 'Saved' : 'Save';
          } else if (!btn.querySelector('svg')) {
            btn.textContent = data.favorited ? 'Saved' : 'Save';
          }
          showToast(data.message, 'success');
        } else {
          if (labelSpan && origText) labelSpan.textContent = origText;
          btn.classList.add('is-error');
          setTimeout(() => btn.classList.remove('is-error'), 1200);
          showToast(data.message || 'Error updating favorite', 'error');
        }
      } catch (err) {
        console.error('Favorite error:', err);
        if (labelSpan && origText) labelSpan.textContent = origText;
        btn.classList.add('is-error');
        setTimeout(() => btn.classList.remove('is-error'), 1200);
        showToast('Unable to update favorite right now.', 'error');
      } finally {
        btn.style.pointerEvents = '';
        btn.style.opacity = '';
      }
    });
  });

  // Rich Share Event handler with native share or clipboard fallback
  document.querySelectorAll('.share-event-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const title = btn.dataset.shareTitle || document.title;
      const occasion = btn.dataset.shareOccasion || '';
      const location = btn.dataset.shareLocation || '';
      const time = btn.dataset.shareTime || '';
      const availability = btn.dataset.shareAvailability || '';
      const directions = btn.dataset.shareDirections || '';
      const url = btn.dataset.shareUrl || window.location.href;

      let shareText = `🍲 Free Food: ${title}\n`;
      if (occasion) shareText += `✨ Occasion: ${occasion}\n`;
      if (availability) shareText += `⚡ Availability: ${availability}\n`;
      if (time) shareText += `⏰ Time: ${time}\n`;
      if (location) shareText += `📍 Location: ${location}\n`;
      if (directions) shareText += `🗺️ Directions: ${directions}\n`;
      shareText += `🔗 View on Free Food: ${url}`;

      // Immediate button tap feedback
      btn.classList.add('is-active-feedback');
      setTimeout(() => btn.classList.remove('is-active-feedback'), 300);

      try {
        if (navigator.share) {
          await navigator.share({
            title: title,
            text: shareText,
            url: url
          });
          return;
        }

        await copyTextToClipboard(shareText);
        showToast('Event details copied! Ready to share.', 'success');
      } catch (err) {
        if (err && err.name !== 'AbortError') {
          showToast('Unable to share this event right now.', 'error');
        }
      }
    });
  });

  // Directions button immediate interaction feedback
  document.querySelectorAll('.btn-directions').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.style.transform = 'scale(0.96)';
      btn.style.opacity = '0.75';
      const label = btn.querySelector('span');
      const origText = label ? label.textContent : null;
      if (label && origText && !origText.includes('Opening')) {
        label.textContent = 'Opening directions...';
      }
      setTimeout(() => {
        btn.style.transform = '';
        btn.style.opacity = '';
        if (label && origText) label.textContent = origText;
      }, 1200);
    });
  });

  // Instant File & Image Upload Visual Feedback
  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      const parent = input.closest('.form-group') || input.parentElement;
      const prevFeedback = parent.querySelector('.file-upload-feedback');
      if (prevFeedback) prevFeedback.remove();

      const feedback = document.createElement('div');
      feedback.className = 'file-upload-feedback';

      const isImage = file.type.startsWith('image/');
      const fileSizeKb = Math.round(file.size / 1024);
      const sizeStr = fileSizeKb > 1024 ? `${(fileSizeKb / 1024).toFixed(1)} MB` : `${fileSizeKb} KB`;

      if (isImage) {
        const reader = new FileReader();
        reader.onload = (re) => {
          feedback.innerHTML = `
            <img src="${re.target.result}" class="file-upload-preview" alt="Preview">
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 700; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</div>
              <div style="font-size: 0.8rem; color: #16a34a; font-weight: 600; display: flex; align-items: center; gap: 0.35rem; margin-top: 2px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Ready to upload (${sizeStr})</span>
              </div>
            </div>
          `;
        };
        reader.readAsDataURL(file);
      } else {
        feedback.innerHTML = `
          <div style="flex: 1; min-width: 0;">
            <div style="font-weight: 700; color: #0f172a;">${file.name} (${sizeStr})</div>
            <div style="font-size: 0.8rem; color: #16a34a; font-weight: 600;">Ready to upload</div>
          </div>
        `;
      }
      parent.appendChild(feedback);
    });
  });

  // Global Community Report Modal Form Handler
  const globalReportForm = document.getElementById('globalReportForm');
  if (globalReportForm) {
    globalReportForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('btnGlobalReportSubmit');
      if (window.InteractionFeedback) {
        window.InteractionFeedback.setButtonLoading(submitBtn, 'Submitting report...');
      } else {
        submitBtn.disabled = true;
      }

      try {
        const res = await fetch(globalReportForm.action, {
          method: 'POST',
          body: new FormData(globalReportForm),
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        const data = await res.json();
        if (data.status === 'success') {
          if (window.InteractionFeedback) {
            window.InteractionFeedback.setButtonSuccess(submitBtn, 'Report submitted');
          }
          if (typeof showToast === 'function') {
            showToast(data.message || 'Report submitted', 'success');
          }
          setTimeout(() => {
            closeModal('globalReportModal');
            globalReportForm.reset();
            if (window.InteractionFeedback) {
              window.InteractionFeedback.restoreButton(submitBtn);
            }
          }, 600);
        } else {
          if (data.require_login) {
            window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
            return;
          }
          if (window.InteractionFeedback) {
            window.InteractionFeedback.setButtonError(submitBtn, 'Failed');
          }
          if (typeof showToast === 'function') {
            showToast(data.message || 'Unable to submit report.', 'error');
          }
        }
      } catch (err) {
        console.error('Report submission error:', err);
        if (window.InteractionFeedback) {
          window.InteractionFeedback.setButtonError(submitBtn, 'Error');
        }
        if (typeof showToast === 'function') {
          showToast('Unable to submit report at this time.', 'error');
        }
      }
    });
  }

  // Close modals when clicking backdrop
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-backdrop')) {
      e.target.classList.remove('is-active');
      document.body.style.overflow = '';
    }
  });

  // Close modals on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.is-active, .modal-backdrop.is-active').forEach(modal => {
        modal.classList.remove('is-active');
      });
      document.body.style.overflow = '';
    }
  });
});

/**
 * Global Report Modal Opener
 */
window.openReportModal = function(eventId, eventTitle) {
  const modal = document.getElementById('globalReportModal');
  if (!modal) return;
  const titleEl = document.getElementById('globalReportEventTitle');
  if (titleEl) {
    titleEl.textContent = eventTitle || 'Event';
  }
  const form = document.getElementById('globalReportForm');
  if (form) {
    form.action = `/food/${eventId}/report/`;
    form.reset();
  }
  const signInBtn = document.getElementById('globalReportSignInBtn');
  if (signInBtn) {
    signInBtn.href = `/login/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
  }
  openModal('globalReportModal');
};

/* ==========================================================================
   Interaction Feedback Engine (Tap, Loading States, Spinners & Progress Bar)
   ========================================================================== */
const InteractionFeedback = {
  _topBarTimeout: null,
  _topBarInterval: null,

  getTopBar() {
    let bar = document.getElementById('topProgressBar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'topProgressBar';
      document.body.appendChild(bar);
    }
    return bar;
  },

  startTopProgress() {
    const bar = this.getTopBar();
    clearTimeout(this._topBarTimeout);
    clearInterval(this._topBarInterval);

    bar.classList.remove('is-done');
    bar.classList.add('is-active');
    bar.style.width = '24%';

    let current = 24;
    this._topBarInterval = setInterval(() => {
      if (current < 82) {
        current += Math.random() * 8 + 3;
        bar.style.width = Math.min(current, 82) + '%';
      }
    }, 180);
  },

  finishTopProgress() {
    const bar = this.getTopBar();
    clearInterval(this._topBarInterval);
    bar.style.width = '100%';
    this._topBarTimeout = setTimeout(() => {
      bar.classList.add('is-done');
      this._topBarTimeout = setTimeout(() => {
        bar.classList.remove('is-active', 'is-done');
        bar.style.width = '0%';
      }, 350);
    }, 150);
  },

  /**
   * Puts a button in an immediate loading state with spinner and prevents repeated clicks
   */
  setButtonLoading(btn, text) {
    if (!btn || btn.classList.contains('is-loading')) return;

    if (!btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }

    const currentWidth = btn.offsetWidth;
    if (currentWidth > 0 && !btn.style.minWidth) {
      btn.style.minWidth = currentWidth + 'px';
    }

    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    btn.classList.add('is-loading');
    btn.classList.remove('is-error', 'is-success');

    let displayText = text || 'Please wait...';
    if (window.I18N && typeof window.I18N.t === 'function') {
      displayText = window.I18N.t(displayText) || displayText;
    }

    btn.innerHTML = `<span class="btn-spinner" aria-hidden="true"></span><span class="btn-loading-label">${displayText}</span>`;

    // Safety timeout: auto restore if response takes over 18 seconds
    clearTimeout(btn._safetyTimeout);
    btn._safetyTimeout = setTimeout(() => {
      if (btn.classList.contains('is-loading')) {
        InteractionFeedback.restoreButton(btn);
      }
    }, 18000);
  },

  /**
   * Restores button to its normal interactive state
   */
  restoreButton(btn) {
    if (!btn) return;
    clearTimeout(btn._safetyTimeout);
    if (btn.dataset.origHtml) {
      btn.innerHTML = btn.dataset.origHtml;
      delete btn.dataset.origHtml;
    }
    btn.style.minWidth = '';
    btn.disabled = false;
    btn.removeAttribute('aria-busy');
    btn.classList.remove('is-loading', 'is-error', 'is-success');
  },

  /**
   * Shows error state on button (red shake, failure icon/label) and restores after duration
   */
  setButtonError(btn, text, duration = 2500) {
    if (!btn) return;
    clearTimeout(btn._safetyTimeout);
    if (!btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }
    btn.classList.remove('is-loading', 'is-success');
    btn.classList.add('is-error');

    let displayText = text || 'Action failed';
    if (window.I18N && typeof window.I18N.t === 'function') {
      displayText = window.I18N.t(displayText) || displayText;
    }

    btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:0.35rem;vertical-align:-0.15em;"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg><span>${displayText}</span>`;

    setTimeout(() => {
      this.restoreButton(btn);
    }, duration);
  },

  /**
   * Shows success state on button (green checkmark, success label)
   */
  setButtonSuccess(btn, text, duration = 1400) {
    if (!btn) return;
    clearTimeout(btn._safetyTimeout);
    if (!btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }
    btn.classList.remove('is-loading', 'is-error');
    btn.classList.add('is-success');

    let displayText = text || 'Success!';
    if (window.I18N && typeof window.I18N.t === 'function') {
      displayText = window.I18N.t(displayText) || displayText;
    }

    btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:0.35rem;vertical-align:-0.15em;"><polyline points="20 6 9 17 4 12"></polyline></svg><span>${displayText}</span>`;

    setTimeout(() => {
      this.restoreButton(btn);
    }, duration);
  },

  /**
   * Adds an immediate visual ripple / tap flash to any clicked button
   */
  addTapFlash(target, e) {
    if (!target) return;
    const flash = document.createElement('span');
    flash.className = 'btn-tap-flash';
    if (e && e.clientX && e.clientY) {
      const rect = target.getBoundingClientRect();
      flash.style.left = (e.clientX - rect.left) + 'px';
      flash.style.top = (e.clientY - rect.top) + 'px';
    }
    target.appendChild(flash);
    setTimeout(() => flash.remove(), 400);
  }
};
window.InteractionFeedback = InteractionFeedback;

// 1. Universal Form Submission Handler
document.addEventListener('submit', (e) => {
  const form = e.target;
  if (!form || form.tagName !== 'FORM') return;

  if (typeof form.checkValidity === 'function' && !form.checkValidity()) {
    return;
  }

  const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], .btn-primary:not([type="button"]), .btn-danger:not([type="button"])');
  if (!submitBtn) return;

  let loadingText = 'Processing...';
  const btnText = (submitBtn.textContent || '').trim().toLowerCase();
  const formAction = (form.getAttribute('action') || '').toLowerCase();

  if (btnText.includes('sign in') || btnText.includes('log in') || formAction.includes('login')) {
    loadingText = 'Signing in...';
  } else if (btnText.includes('create') || btnText.includes('register') || formAction.includes('register')) {
    loadingText = 'Creating account...';
  } else if (btnText.includes('submit') || formAction.includes('event_add') || formAction.includes('add')) {
    loadingText = 'Submitting...';
  } else if (btnText.includes('find food') || btnText.includes('near me')) {
    loadingText = 'Finding food...';
  } else if (btnText.includes('search') || formAction.includes('search')) {
    loadingText = 'Searching...';
  } else if (btnText.includes('detect') || formAction.includes('location')) {
    loadingText = 'Detecting location...';
  } else if (btnText.includes('report') || formAction.includes('report')) {
    loadingText = 'Submitting report...';
  } else if (btnText.includes('save') || btnText.includes('saved')) {
    loadingText = 'Saving...';
  } else if (btnText.includes('filter') || formAction.includes('event_list')) {
    loadingText = 'Filtering...';
  } else if (btnText.includes('reset') || formAction.includes('password_reset')) {
    loadingText = 'Sending instructions...';
  } else if (btnText.includes('claim')) {
    loadingText = 'Confirming claim...';
  } else if (btnText.includes('approve')) {
    loadingText = 'Approving...';
  } else if (btnText.includes('reject')) {
    loadingText = 'Rejecting...';
  }

  InteractionFeedback.setButtonLoading(submitBtn, loadingText);
  InteractionFeedback.startTopProgress();
});

// 2. Universal Click & Navigation Feedback
document.addEventListener('click', (e) => {
  const clickable = e.target.closest('.btn, button, .fav-btn, .location-change, .alert-close, .lang-btn, .pill-tab, .btn-card-action');
  if (clickable) {
    InteractionFeedback.addTapFlash(clickable, e);
  }

  const link = e.target.closest('a[href]');
  if (!link) return;

  const href = link.getAttribute('href');
  if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('tel:') || href.startsWith('mailto:')) {
    return;
  }
  if (link.target === '_blank' || link.hasAttribute('download')) {
    return;
  }
  if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
    return;
  }

  // If clicked a button styled as link
  if (link.classList.contains('btn') && !link.classList.contains('is-loading')) {
    const text = (link.textContent || '').trim().toLowerCase();
    let loadingMsg = 'Loading...';
    if (text.includes('near me') || text.includes('find food')) {
      loadingMsg = 'Finding food...';
    } else if (text.includes('details') || text.includes('view')) {
      loadingMsg = 'Opening event...';
    } else if (text.includes('map')) {
      loadingMsg = 'Opening map...';
    } else if (text.includes('sign in') || text.includes('log in')) {
      loadingMsg = 'Signing in...';
    }
    InteractionFeedback.setButtonLoading(link, loadingMsg);
  }

  InteractionFeedback.startTopProgress();
});

// 3. Reset states on page show / bfcache restore
window.addEventListener('pageshow', () => {
  InteractionFeedback.finishTopProgress();
  document.querySelectorAll('.is-loading').forEach(btn => {
    InteractionFeedback.restoreButton(btn);
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
  if (modal) {
    modal.classList.add('is-active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('is-active');
    document.body.style.overflow = '';
  }
}
