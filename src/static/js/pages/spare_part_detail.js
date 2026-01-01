document.addEventListener('DOMContentLoaded', () => {
  // Handle delete confirmation buttons
  document.querySelectorAll('.delete-confirm-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const form = btn.closest('form');
      const message = btn.dataset.confirmMessage;

      showDeleteConfirm(form, message);
    });
  });
});
