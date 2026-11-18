document.querySelectorAll('main form').forEach(form => {
  const error = form.querySelector('.content_error');
  if (!error) return;

  const inputs = form.querySelectorAll('.info input');
  const fieldErrors = form.querySelectorAll('[data-field-error]');
  const hasError = error.textContent.trim() !== '';
  error.hidden = !hasError;

  if (hasError) {
    inputs.forEach(input => {
      input.classList.add('err');
      input.setAttribute('aria-invalid', 'true');
    });
  }

  fieldErrors.forEach(message => {
    const hasFieldError = message.textContent.trim() !== '';
    message.hidden = !hasFieldError;
    if (hasFieldError) {
      const input = form.querySelector(`input[name="${message.dataset.fieldError}"]`);
      if (input) {
        input.classList.add('err');
        input.setAttribute('aria-invalid', 'true');
      }
    }
  });

  function clearError() {
    inputs.forEach(input => {
      input.classList.remove('err');
      input.removeAttribute('aria-invalid');
    });
    error.textContent = '';
    error.hidden = true;
    fieldErrors.forEach(message => {
      message.textContent = '';
      message.hidden = true;
    });
  }

  inputs.forEach(input => {
    input.addEventListener('input', clearError);
    input.addEventListener('change', clearError);
  });
});
