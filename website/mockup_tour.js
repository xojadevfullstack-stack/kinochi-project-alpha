(function () {
  function injectTourAssets() {
    if (!document.getElementById('apple-onboarding-tour')) {
      const style = document.createElement('style');
      style.id = 'apple-onboarding-tour';
      style.textContent = `
        #onboardingCard {
          background-color: rgba(18, 20, 29, 0.94) !important;
          backdrop-filter: blur(26px) saturate(180%) !important;
          -webkit-backdrop-filter: blur(26px) saturate(180%) !important;
          border: 1px solid rgba(255, 255, 255, 0.16) !important;
          color: #FFFFFF !important;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65) !important;
        }
        body.light-theme #onboardingCard {
          background-color: rgba(255, 255, 255, 0.96) !important;
          border: 1px solid rgba(15, 23, 42, 0.12) !important;
          color: #0F172A !important;
          box-shadow: 0 20px 45px rgba(15, 23, 42, 0.16) !important;
        }
        body.light-theme #onboardingTitle { color: #0F172A !important; }
        body.light-theme #onboardingDesc { color: #475569 !important; }
        body.light-theme #onboardingSkipBtn { color: #64748B !important; }
        body.light-theme #onboardingBackBtn {
          background-color: #F1F5F9 !important;
          color: #334155 !important;
          border: 1px solid #CBD5E1 !important;
        }
        #onboardingNextBtn {
          background-color: #E50914 !important;
          color: #FFFFFF !important;
        }
        #onboardingNextBtn:hover {
          background-color: #B80710 !important;
          color: #FFFFFF !important;
        }
      `;
      document.head.appendChild(style);
    }

    if (!document.getElementById('onboardingRoot')) {
      const wrap = document.createElement('div');
      wrap.id = 'onboardingRoot';
      wrap.className = 'hidden fixed inset-0 z-[120]';
      wrap.setAttribute('role', 'dialog');
      wrap.setAttribute('aria-modal', 'true');
      wrap.innerHTML = `
        <div id="onboardingBackdrop" class="absolute inset-0 bg-transparent"></div>
        <div id="onboardingRing" class="fixed pointer-events-none rounded-2xl border-2 border-[#E50914] transition-all duration-300" style="box-shadow: 0 0 0 9999px rgba(4, 6, 12, 0.72), 0 0 24px rgba(229, 9, 20, 0.45);"></div>
        <div id="onboardingCard" class="fixed z-[125] w-[310px] rounded-2xl p-4 transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <span id="onboardingBadge" class="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-red/15 text-brand-red border border-brand-red/30">Qadam</span>
            <span id="onboardingCounter" class="text-[11px] font-mono text-gray-400">1 / 3</span>
          </div>
          <h3 id="onboardingTitle" class="font-outfit font-bold text-sm leading-snug mb-1 text-white"></h3>
          <p id="onboardingDesc" class="text-xs text-gray-300 leading-relaxed mb-3.5"></p>
          <div class="flex items-center justify-between gap-2">
            <button id="onboardingSkipBtn" type="button" class="text-[11px] font-semibold text-gray-400 hover:text-white transition cursor-pointer">O'tkazib yuborish</button>
            <div class="flex items-center gap-1.5">
              <button id="onboardingBackBtn" type="button" class="hidden px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/15 text-gray-200 transition cursor-pointer">Orqaga</button>
              <button id="onboardingNextBtn" type="button" class="px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-md transition cursor-pointer">Keyingi ›</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(wrap);
      document.getElementById('onboardingBackdrop').onclick = finishOnboardingTour;
      document.getElementById('onboardingSkipBtn').onclick = finishOnboardingTour;
      document.getElementById('onboardingBackBtn').onclick = function () { stepOnboardingTour(-1); };
      document.getElementById('onboardingNextBtn').onclick = function () { stepOnboardingTour(1); };
    }
  }

  let stepIdx = 0;
  let active = false;

  function findTarget(selectors) {
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      const isFixed = getComputedStyle(el).position === 'fixed';
      if (r.width > 0 && r.height > 0 && (el.offsetParent !== null || isFixed)) return el;
    }
    return null;
  }

  function positionStep(shouldScroll) {
    const cfg = window.MEDIAPLUS_TOUR_CONFIG;
    if (!active || !cfg || !cfg.steps || !cfg.steps[stepIdx]) return;
    const step = cfg.steps[stepIdx];
    const ring = document.getElementById('onboardingRing');
    const card = document.getElementById('onboardingCard');
    document.getElementById('onboardingBadge').textContent = step.badge;
    document.getElementById('onboardingCounter').textContent = (stepIdx + 1) + ' / ' + cfg.steps.length;
    document.getElementById('onboardingTitle').textContent = step.title;
    document.getElementById('onboardingDesc').textContent = step.desc;
    document.getElementById('onboardingBackBtn').classList.toggle('hidden', stepIdx === 0);
    document.getElementById('onboardingNextBtn').textContent = stepIdx === cfg.steps.length - 1 ? 'Tushunarli ✓' : 'Keyingi ›';

    const target = findTarget(step.selectors);
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    if (target && shouldScroll) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    const apply = function () {
      if (!active) return;
      const r = target ? target.getBoundingClientRect() : null;
      if (r) {
        const pad = 6;
        ring.style.display = 'block';
        ring.style.top = Math.max(4, r.top - pad) + 'px';
        ring.style.left = Math.max(4, r.left - pad) + 'px';
        ring.style.width = Math.min(vw - 8, r.width + pad * 2) + 'px';
        ring.style.height = (r.height + pad * 2) + 'px';
        const above = r.bottom + 215 > vh && r.top > 215;
        card.style.top = (above ? Math.max(16, r.top - 200) : Math.min(vh - 208, r.bottom + 14)) + 'px';
        card.style.left = Math.min(Math.max(12, r.left + r.width / 2 - 155), Math.max(12, vw - 322)) + 'px';
      } else {
        ring.style.display = 'none';
        card.style.top = Math.max(80, vh / 2 - 95) + 'px';
        card.style.left = Math.max(12, vw / 2 - 155) + 'px';
      }
    };
    apply();
    if (shouldScroll && target) setTimeout(apply, 320);
  }

  window.startOnboardingTour = function () {
    const cfg = window.MEDIAPLUS_TOUR_CONFIG;
    if (!cfg || !cfg.steps || !cfg.steps.length) return;
    injectTourAssets();
    stepIdx = 0;
    active = true;
    try { localStorage.setItem(cfg.storageKey, 'done'); } catch (e) {}
    document.getElementById('onboardingRoot').classList.remove('hidden');
    positionStep(true);
  };

  window.stepOnboardingTour = function (delta) {
    const cfg = window.MEDIAPLUS_TOUR_CONFIG;
    if (!cfg) return;
    const next = stepIdx + delta;
    if (next >= cfg.steps.length) { finishOnboardingTour(); return; }
    stepIdx = Math.max(0, next);
    positionStep(true);
  };

  window.finishOnboardingTour = function () {
    const cfg = window.MEDIAPLUS_TOUR_CONFIG;
    active = false;
    const root = document.getElementById('onboardingRoot');
    if (root) root.classList.add('hidden');
    if (cfg) { try { localStorage.setItem(cfg.storageKey, 'done'); } catch (e) {} }
  };

  function boot() {
    const cfg = window.MEDIAPLUS_TOUR_CONFIG;
    if (!cfg) return;
    try {
      if (localStorage.getItem(cfg.storageKey) !== 'done') {
        setTimeout(function () { window.startOnboardingTour(); }, 850);
      }
    } catch (e) {}
    window.addEventListener('resize', function () { positionStep(false); });
    window.addEventListener('scroll', function () { positionStep(false); }, { passive: true });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && active) window.finishOnboardingTour();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
