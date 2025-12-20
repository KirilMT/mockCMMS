// Event handling methods

/**
 * Attaches event listeners to table controls (buttons, search, sorting).
 * Handles global search, clearing filters, exporting, and configuration saving.
 */
AdvancedTable.prototype.attachEventListeners = function () {
  const buttons = this.container.querySelectorAll('[data-action]');
  buttons.forEach((button) => {
    const action = button.getAttribute('data-action');

    if (action === 'clearAllFilters') {
      button.addEventListener('click', () => this.resetTableState());
    } else if (action === 'exportData') {
      button.addEventListener('click', () => this.exportData('csv'));
    } else if (action === 'saveConfiguration') {
      button.addEventListener('click', () => this.saveConfiguration());
    }
  });

  const searchInput = document.getElementById('globalSearchInput');
  const applySearchBtn = document.getElementById('applySearchBtn');
  const clearSearchBtn = document.getElementById('clearSearchBtn');

  if (searchInput && applySearchBtn) {
    // Initial state
    applySearchBtn.disabled = !searchInput.value.trim();

    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const value = e.target.value;
        this.globalSearch(value);
        if (clearSearchBtn) {
          clearSearchBtn.style.display = value ? 'inline-block' : 'none';
        }
      }
    });

    searchInput.addEventListener('input', (e) => {
      const value = e.target.value;
      // Update Apply button state
      applySearchBtn.disabled = !value.trim();

      if (clearSearchBtn) {
        clearSearchBtn.style.display = value ? 'inline-block' : 'none';
      }
    });
  }

  if (applySearchBtn) {
    applySearchBtn.addEventListener('click', () => {
      if (searchInput) {
        const value = searchInput.value;
        this.globalSearch(value);
        if (clearSearchBtn) {
          clearSearchBtn.style.display = value ? 'inline-block' : 'none';
        }
      }
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        // Disable Apply button when cleared
        if (applySearchBtn) applySearchBtn.disabled = true;

        clearSearchBtn.style.display = 'none';
        this.globalSearch('');
      }
    });
  }

  const headers = this.container.querySelectorAll(
    '.advanced-table th.sortable'
  );
  headers.forEach((header) => {
    header.addEventListener('click', (e) => {
      // Ignore clicks that originated from resize handle
      if (
        e.target.classList.contains('resize-handle') ||
        e.target.closest('.resize-handle')
      ) {
        e.stopPropagation();
        e.preventDefault();
        return;
      }

      const column = header.getAttribute('data-column');
      this.sort(column);
    });
  });
};
