document.addEventListener('DOMContentLoaded', function() {
  /**
   * Enables or disables the save button on a checklist item form based on whether 
   * the status or comment has changed from its initial value.
   * 
   * @param {HTMLFormElement} form The checklist item form element.
   */
  function checkItemChanged(form) {
    const statusSelect = form.querySelector('select[name="mark_status"]');
    const commentInput = form.querySelector('input[name="comment"]');
    const saveButton = form.querySelector('button.item-save-btn');

    // Ensure elements exist before proceeding
    if (!statusSelect || !commentInput || !saveButton) {
      console.warn('Required form elements not found in:', form);
      return;
    }

    const initialStatus = statusSelect.getAttribute('data-initial-status') || 'not_started';
    const initialComment = commentInput.getAttribute('data-initial-comment') || '';

    const statusChanged = statusSelect.value !== initialStatus;
    const commentChanged = commentInput.value !== initialComment;

    // Enable the button only if status or comment has changed
    saveButton.disabled = !(statusChanged || commentChanged);
  }

  // Select all forms with the class 'item-update-form'
  const itemForms = document.querySelectorAll('form.item-update-form');

  // Initialize and add event listeners to each form
  itemForms.forEach(form => {
    const statusSelect = form.querySelector('select[name="mark_status"]');
    const commentInput = form.querySelector('input[name="comment"]');

    // Set initial data attributes if they don't exist (e.g., on first load)
    if (statusSelect && !statusSelect.hasAttribute('data-initial-status')) {
        statusSelect.setAttribute('data-initial-status', statusSelect.value);
    }
    if (commentInput && !commentInput.hasAttribute('data-initial-comment')) {
        commentInput.setAttribute('data-initial-comment', commentInput.value);
    }

    // Perform initial check
    checkItemChanged(form);

    // Add event listener for changes within the form
    form.addEventListener('input', () => checkItemChanged(form));

    // Optional: Re-evaluate on form reset if you add reset buttons
    // form.addEventListener('reset', () => setTimeout(() => checkItemChanged(form), 0));
  });

  console.log(`Checklist item change listeners initialized for ${itemForms.length} forms.`);

}); 