// Health Research Journal — client-side helpers

// Show spinner and disable submit button on form submission
document.addEventListener('DOMContentLoaded', function () {
  const forms = [
    { form: 'link-form', btn: 'link-submit-btn', spinner: 'link-spinner' },
    { form: 'file-form', btn: 'file-submit-btn', spinner: 'file-spinner' },
    { form: 'text-form', btn: 'text-submit-btn', spinner: 'text-spinner' },
  ];

  forms.forEach(function ({ form, btn, spinner }) {
    const formEl = document.getElementById(form);
    const btnEl  = document.getElementById(btn);
    const spEl   = document.getElementById(spinner);
    if (!formEl || !btnEl) return;

    formEl.addEventListener('submit', function () {
      btnEl.disabled = true;
      if (spEl) spEl.classList.remove('d-none');
      btnEl.querySelector('span:last-child') || (btnEl.textContent = 'Processing...');
    });
  });
});
