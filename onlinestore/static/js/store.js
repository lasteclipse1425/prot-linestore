(() => {
    const root = document.documentElement;
    const toggle = document.querySelector('[data-theme-toggle]');
    const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    const readSavedTheme = () => {
        try {
            const theme = localStorage.getItem('store-theme');
            return theme === 'dark' || theme === 'light' ? theme : null;
        } catch (_) {
            return null;
        }
    };

    const savedTheme = readSavedTheme();
    if (!savedTheme && media) root.dataset.theme = media.matches ? 'dark' : 'light';

    const updateToggle = () => {
        if (!toggle) return;
        const dark = root.dataset.theme === 'dark';
        toggle.setAttribute('aria-pressed', String(dark));
        toggle.setAttribute('aria-label', dark ? toggle.dataset.lightLabel : toggle.dataset.darkLabel);
        toggle.querySelector('.theme-toggle__icon').textContent = dark ? '☀' : '☾';
        toggle.querySelector('.theme-toggle__text').textContent = dark ? toggle.dataset.lightText : toggle.dataset.darkText;
    };

    updateToggle();
    if (toggle) {
        toggle.addEventListener('click', () => {
            const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
            root.dataset.theme = next;
            try { localStorage.setItem('store-theme', next); } catch (_) { /* Theme still works for this page. */ }
            updateToggle();
        });
    }

    if (media && !savedTheme) {
        media.addEventListener('change', (event) => {
            root.dataset.theme = event.matches ? 'dark' : 'light';
            updateToggle();
        });
    }
})();
