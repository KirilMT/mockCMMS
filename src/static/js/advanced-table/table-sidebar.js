/**
 * Sidebar functionality for Advanced Table
 * Handles sidebar toggle, section expand/collapse, and state persistence
 */
class TableSidebar {
  /**
   * Create a new TableSidebar instance.
   * @param {AdvancedTable} advancedTable - The parent AdvancedTable instance.
   */
  constructor(advancedTable) {
    this.table = advancedTable;
    // Use global StorageManager or a safe dummy if not available
    const SafeStorage = window.StorageManager || {
      get: () => null,
      set: () => {},
      remove: () => {},
    };

    let collapsed = "false";
    let sections = "[]";

    collapsed = SafeStorage.get("tableSidebarCollapsed", "false");
    sections = SafeStorage.get("tableSidebarSections", "[]");
    this.sidebarCollapsed = collapsed === "true";
    try {
      this.expandedSections = JSON.parse(sections) || [];
    } catch (_) {
      // Ignore error
      this.expandedSections = [];
    }
  }

  /**
   * Generate sidebar HTML structure
   * @returns {string} The HTML string for the sidebar.
   */
  generateHTML() {
    return `
            <div class="table-sidebar ${
              this.sidebarCollapsed ? "collapsed" : ""
            }">
                <div class="sidebar-header">
                    <h6>Table Controls</h6>
                    <button class="btn-collapse" title="Collapse sidebar">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                </div>

                <!-- Filters Section -->
                <div class="sidebar-section" data-section="filters">
                    <div class="section-header ${
                      this.expandedSections.includes("filters")
                        ? "expanded"
                        : ""
                    }">
                        <i class="fas fa-filter"></i>
                        <span>Filters</span>
                        <span class="badge">0</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${
                      this.expandedSections.includes("filters")
                        ? ""
                        : "collapsed"
                    }">
                        <div id="filterRows">
                            <!-- Filter rows will be populated here -->
                            <p class="empty-state-message" id="noFiltersMessage">No applied filters</p>
                        </div>
                        <div class="filter-actions" style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                            <button class="btn btn-sm btn-outline-primary" id="addFilterBtn" style="flex: 1;">
                                <i class="fas fa-plus"></i> Add
                            </button>
                            <button class="btn btn-sm btn-primary" id="applyFiltersBtn" style="flex: 2;">
                                <i class="fas fa-check"></i> Apply
                            </button>
                            <button class="btn btn-sm btn-outline-danger" id="clearFiltersBtn" style="flex: 1;">
                                <i class="fas fa-times"></i> Clear
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Columns Section -->
                <div class="sidebar-section" data-section="columns">
                    <div class="section-header ${
                      this.expandedSections.includes("columns")
                        ? "expanded"
                        : ""
                    }">
                        <i class="fas fa-columns"></i>
                        <span>Columns</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${
                      this.expandedSections.includes("columns")
                        ? ""
                        : "collapsed"
                    }">
                        <div id="columnList" class="column-list">
                            <!-- Column items will be populated here -->
                        </div>
                        <div class="column-actions" style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                            <button class="btn btn-sm btn-primary" id="applyColumnsBtn" style="flex: 1;">
                                <i class="fas fa-check"></i> Apply
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" id="resetColumnsBtn" style="flex: 1;">
                                <i class="fas fa-undo"></i> Reset
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Collaboration Section -->
                <div class="sidebar-section" data-section="collaboration">
                    <div class="section-header ${
                      this.expandedSections.includes("collaboration")
                        ? "expanded"
                        : ""
                    }">
                        <i class="fas fa-users"></i>
                        <span>Active Users</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${
                      this.expandedSections.includes("collaboration")
                        ? ""
                        : "collapsed"
                    }">
                        <div id="activeUsersList" class="active-users-list">
                            <p class="empty-state-message">Checking for active users...</p>
                        </div>
                    </div>
                </div>

                <!-- Saved Views Section -->
                <div class="sidebar-section" data-section="configs">
                    <div class="section-header ${
                      this.expandedSections.includes("configs")
                        ? "expanded"
                        : ""
                    }">
                        <i class="fas fa-save"></i>
                        <span>Saved Views</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${
                      this.expandedSections.includes("configs")
                        ? ""
                        : "collapsed"
                    }">
                        <div id="savedViewsList" class="saved-views-list">
                            <!-- Saved views will be populated here -->
                        </div>
                        <div class="config-actions" style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                            <button class="btn btn-sm btn-success" id="saveViewBtn" style="flex: 1;">
                                <i class="fas fa-save"></i> Save
                            </button>
                            <button class="btn btn-sm btn-primary" id="updateViewBtn" style="flex: 1;" disabled>
                                <i class="fas fa-sync"></i> Update
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  /**
   * Attach event listeners to sidebar elements
   */
  attachEventListeners() {
    // Toggle sidebar collapse
    const collapseBtn = document.querySelector(".btn-collapse");
    if (collapseBtn) {
      collapseBtn.addEventListener("click", () => this.toggleSidebar());
    }

    const toggleBtn = document.querySelector(".btn-toggle-sidebar");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => this.toggleSidebar());
    }

    // Section expand/collapse
    const sectionHeaders = document.querySelectorAll(".section-header");
    sectionHeaders.forEach((header) => {
      header.addEventListener("click", () => {
        const section = header.closest(".sidebar-section").dataset.section;
        this.toggleSection(section);
      });
    });

    // Add Filter button
    const addFilterBtn = document.getElementById("addFilterBtn");
    if (addFilterBtn) {
      addFilterBtn.addEventListener("click", () => this.addFilterRow());
    }

    // Apply Filters button
    const applyFiltersBtn = document.getElementById("applyFiltersBtn");
    if (applyFiltersBtn) {
      applyFiltersBtn.addEventListener("click", () => {
        // Force remove editing state when explicitly applied
        document
          .querySelectorAll(".is-editing")
          .forEach((el) => el.classList.remove("is-editing"));
        this.applyAllFilters();
      });
    }

    // Clear All Filters button
    const clearFiltersBtn = document.getElementById("clearFiltersBtn");
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener("click", () => this.clearAllFilters());
    }

    // Apply Columns button
    const applyColumnsBtn = document.getElementById("applyColumnsBtn");
    if (applyColumnsBtn) {
      applyColumnsBtn.addEventListener("click", () =>
        this.applyColumnChanges(),
      );
    }

    // Reset Columns button
    const resetColumnsBtn = document.getElementById("resetColumnsBtn");
    if (resetColumnsBtn) {
      resetColumnsBtn.addEventListener("click", () => this.resetColumns());
    }

    // Save View button
    const saveViewBtn = document.getElementById("saveViewBtn");
    if (saveViewBtn) {
      saveViewBtn.addEventListener("click", () => this.saveView());
    }

    // Update View button
    const updateViewBtn = document.getElementById("updateViewBtn");
    if (updateViewBtn) {
      updateViewBtn.addEventListener("click", () => this.updateView());
    }

    // Validate filters to set initial button states
    this.validateAllFilters();

    // Start real-time filter visibility polling
    this.startCollaborationPolling();
  }

  /**
   * Toggle sidebar collapsed state.
   */
  toggleSidebar() {
    const sidebar = document.querySelector(".table-sidebar");
    if (!sidebar) return;

    this.sidebarCollapsed = !this.sidebarCollapsed;
    sidebar.classList.toggle("collapsed");

    // Update collapse button icon
    const collapseBtn = document.querySelector(".btn-collapse i");
    if (collapseBtn) {
      collapseBtn.className = this.sidebarCollapsed
        ? "fas fa-chevron-right"
        : "fas fa-chevron-left";
    }

    // Save state
    const SafeStorage = window.StorageManager || {
      get: () => null,
      set: () => {},
      remove: () => {},
    };
    SafeStorage.set("tableSidebarCollapsed", this.sidebarCollapsed);

    // Trigger resize to adjust table width after sidebar toggle
    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 300); // Wait for transition
  }

  /**
   * Toggle section expanded state.
   * @param {string} sectionName - The data-section attribute of the section to toggle.
   */
  toggleSection(sectionName) {
    const section = document.querySelector(
      `.sidebar-section[data-section="${sectionName}"]`,
    );
    if (!section) return;

    const header = section.querySelector(".section-header");
    const content = section.querySelector(".section-content");

    const isExpanded = header.classList.contains("expanded");

    if (isExpanded) {
      // Collapse
      header.classList.remove("expanded");
      content.classList.add("collapsed");
      this.expandedSections = this.expandedSections.filter(
        (s) => s !== sectionName,
      );
    } else {
      // Expand
      header.classList.add("expanded");
      content.classList.remove("collapsed");
      if (!this.expandedSections.includes(sectionName)) {
        this.expandedSections.push(sectionName);
      }
    }

    // Save state
    this.saveExpandedSections();
  }

  /**
   * Saves the current state of expanded sections to localStorage.
   */
  saveExpandedSections() {
    const SafeStorage = window.StorageManager || {
      get: () => null,
      set: () => {},
      remove: () => {},
    };
    SafeStorage.set(
      "tableSidebarSections",
      JSON.stringify(this.expandedSections),
    );
  }

  /**
   * Load existing filters from table into sidebar.
   */
  loadExistingFilters() {
    const filterRows = document.getElementById("filterRows");
    if (!filterRows) return;

    // Clear existing rows
    filterRows.innerHTML = "";

    // Add rows for each existing filter (array format)
    if (Array.isArray(this.table.filters) && this.table.filters.length > 0) {
      this.table.filters.forEach((filter) => {
        this.addFilterRow(
          filter.column,
          filter.operator,
          filter.value,
          filter.logic,
        );
      });
    } else {
      // Show empty state message
      filterRows.innerHTML =
        '<p class="empty-state-message" id="noFiltersMessage">No applied filters</p>';
    }

    // Update badge
    const count = Array.isArray(this.table.filters)
      ? this.table.filters.length
      : 0;
    this.updateFilterBadge(count);

    // ALWAYS validate after loading to set correct button states (even if no filters)
    // Use setTimeout to ensure DOM is fully updated
    setTimeout(() => this.validateAllFilters(), 0);
  }

  /**
   * Add a filter row to the sidebar.
   * @param {string} [column=""] - The column key.
   * @param {string} [operator="contains"] - The filter operator.
   * @param {string} [value=""] - The filter value.
   * @param {string} [logic="AND"] - The logic operator (AND/OR).
   */
  addFilterRow(column = "", operator = "contains", value = "", logic = "AND") {
    const filterRows = document.getElementById("filterRows");
    if (!filterRows) return;

    // Hide "No applied filters" message
    const noFiltersMsg = document.getElementById("noFiltersMessage");
    if (noFiltersMsg) {
      noFiltersMsg.style.display = "none";
    }

    // AUTO-APPLY: If adding a second filter and first is valid, apply first filter
    const existingFilterRows = filterRows.querySelectorAll(
      ".filter-row-sidebar",
    );
    const isAddingSecondFilter = existingFilterRows.length === 1 && !column; // Adding empty row when one exists

    if (isAddingSecondFilter) {
      const firstRow = existingFilterRows[0];
      const firstColumn = firstRow.querySelector(".filter-column")?.value;
      const firstValue = firstRow.querySelector(".filter-value")?.value?.trim();

      // If first filter is complete and valid, apply it before adding second
      if (firstColumn && firstValue) {
        this.applyAllFilters();
      }
    }

    const isFirstRow =
      filterRows.children.length === 0 ||
      (filterRows.children.length === 1 && noFiltersMsg);
    const filterRow = document.createElement("div");
    filterRow.className = "filter-row-sidebar";
    filterRow.style.cssText =
      "display: flex; gap: 0.5rem; margin-bottom: 0.75rem; padding: 0.75rem; background: #f8f9fa; border-radius: 4px; align-items: flex-start;";

    // For non-first rows, add margin-top to create space for the connector
    if (!isFirstRow) {
      filterRow.style.marginTop = "0.5rem";
    }

    filterRow.innerHTML = `
            <div class="filter-inputs" style="flex: 1; display: flex; flex-direction: column; gap: 0.5rem;">
                <select class="form-select form-select-sm filter-column">
                    <option value="">Select Column</option>
                    ${this.table.columnOrder
                      .filter((key) => !this.table.hiddenColumns.has(key))
                      .map((key) => {
                        const col = this.table.columns.find(
                          (c) => c.key === key,
                        );
                        if (!col) return "";
                        return `<option value="${col.key}" ${
                          col.key === column ? "selected" : ""
                        }>${col.label}</option>`;
                      })
                      .join("")}
                </select>
                <select class="form-select form-select-sm filter-operator" ${
                  !column ? "disabled" : ""
                }>
                    <option value="contains" ${
                      operator === "contains" ? "selected" : ""
                    }>Contains</option>
                    <option value="not_contains" ${
                      operator === "not_contains" ? "selected" : ""
                    }>Does Not Contain</option>
                    <option value="equals" ${
                      operator === "equals" ? "selected" : ""
                    }>Equals</option>
                    <option value="not_equals" ${
                      operator === "not_equals" ? "selected" : ""
                    }>Not Equals</option>
                    <option value="starts_with" ${
                      operator === "starts_with" ? "selected" : ""
                    }>Starts With</option>
                    <option value="ends_with" ${
                      operator === "ends_with" ? "selected" : ""
                    }>Ends With</option>
                </select>
                <input type="text" class="form-control form-control-sm filter-value"
                       placeholder="Enter value..." value="${value || ""}" ${
                         !column ? "disabled" : ""
                       }>
            </div>
            <button class="btn btn-sm btn-outline-danger remove-filter-btn" style="align-self: center;">
                <i class="fas fa-times"></i>
            </button>
        `;

    // Add logic connector BETWEEN rows (as a separate element before this row)
    if (!isFirstRow) {
      const connector = document.createElement("div");
      connector.className = "filter-logic-connector";
      connector.style.cssText =
        "display: flex; align-items: center; justify-content: center; margin: 0.5rem 0; gap: 12px; font-size: 0.75rem; color: #6c757d;";
      connector.innerHTML = `
                <div style="flex: 1; height: 1px; background: #dee2e6;"></div>
                <div style="display: flex; gap: 12px; background: white; padding: 2px 12px; border-radius: 4px; border: 1px solid #dee2e6;">
                    <label style="display: flex; align-items: center; gap: 4px; margin: 0; cursor: default;">
                        <input type="radio" class="filter-logic-radio" name="logic-${Date.now()}" value="AND" ${
                          logic !== "OR" ? "checked" : ""
                        }>
                        <span style="pointer-events: none; user-select: none;">AND</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 4px; margin: 0; cursor: default;">
                        <input type="radio" class="filter-logic-radio" name="logic-${Date.now()}" value="OR" ${
                          logic === "OR" ? "checked" : ""
                        }>
                        <span style="pointer-events: none; user-select: none;">OR</span>
                    </label>
                </div>
                <div style="flex: 1; height: 1px; background: #dee2e6;"></div>
            `;
      // Insert connector before the current filter row
      filterRows.appendChild(connector);
    }

    // Insert filter row into container
    filterRows.appendChild(filterRow);

    // Attach event listeners to this row
    this.attachFilterRowListeners(filterRow);

    // Update filter count - only show APPLIED filters, not empty/unapplied rows
    // The badge reflects this.table.filters.length, not DOM row count
    this.updateFilterBadge(this.table.filters ? this.table.filters.length : 0);

    // Re-validate to update button states
    this.validateAllFilters();
  }

  /**
   * Attach event listeners to a filter row.
   * @param {HTMLElement} filterRow - The filter row element.
   */
  attachFilterRowListeners(filterRow) {
    const columnSelect = filterRow.querySelector(".filter-column");
    const operatorSelect = filterRow.querySelector(".filter-operator");
    const valueInput = filterRow.querySelector(".filter-value");
    const removeBtn = filterRow.querySelector(".remove-filter-btn");
    // Logic radios are in the connector BEFORE this row
    const connector = filterRow.previousElementSibling;
    let logicRadios = [];
    if (connector && connector.classList.contains("filter-logic-connector")) {
      logicRadios = connector.querySelectorAll(".filter-logic-radio");
    }

    // State Snapshot for Smart Blur
    let originalState = null;

    // Helper to enforce editing state
    const setEditing = () => {
      if (!filterRow.classList.contains("is-editing")) {
        // First time entering edit mode - snapshot state
        originalState = {
          column: columnSelect.value,
          operator: operatorSelect.value,
          value: valueInput.value.trim(),
        };
      }
      filterRow.classList.add("is-editing");
      this.applyAllFilters();
    };

    // Column selection change
    columnSelect.addEventListener("change", () => {
      const column = columnSelect.value;
      operatorSelect.disabled = !column;
      valueInput.disabled = !column;
      valueInput.placeholder = column
        ? "Filter value"
        : "Select a column first";

      // Refinement: Always clear value when column changes to trigger "Mute" state
      // This ensures the user starts fresh and sees the base data (mute logic)
      valueInput.value = "";

      this.validateAllFilters();
      // Triggers mute logic immediately because value is now empty
      this.applyAllFilters();
    });

    // Toggle "is-editing" class on focus to enable "Edit Mute"
    // User wants the filter to be invalid/muted while being edited
    // Bind to all inputs explicitly to be robust
    [columnSelect, operatorSelect, valueInput].forEach((el) => {
      el.addEventListener("focus", setEditing);
    });

    // Also handle focusout on the row level
    filterRow.addEventListener("focusout", () => {
      // Use timeout to allow focus to move to another element within the same row
      setTimeout(() => {
        // Only proceed if focus has moved OUTSIDE this row entirely
        if (!filterRow.contains(document.activeElement)) {
          // Check if dirty compared to original state
          const col = columnSelect.value;
          const op = operatorSelect.value;
          const val = valueInput.value.trim();

          let isDirty = false;

          if (originalState) {
            if (
              col !== originalState.column ||
              op !== originalState.operator ||
              val !== originalState.value
            ) {
              isDirty = true;
            }
          } else {
            // If no original state was captured (shouldn't happen if setEditing worked), assume dirty if content exists
            if (col || val) isDirty = true;
          }

          if (!isDirty) {
            // Clean (No changes made): Restore functionality (Un-mute)
            filterRow.classList.remove("is-editing");
            originalState = null; // Clear snapshot
            this.applyAllFilters();
          } else {
            // Dirty (Pending Changes): Maintain "Mute" state
            this.applyAllFilters();
          }
        }
      }, 50);
    });

    // ESC key to cancel/revert edits (same as clean blur) - for ALL filter inputs
    // Use keyup: dropdown closes on keydown, then keyup fires and we blur+revert
    [columnSelect, operatorSelect, valueInput].forEach((el) => {
      el.addEventListener("keyup", (e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          e.stopPropagation();
          // Revert to original snapshot if it exists
          if (originalState) {
            columnSelect.value = originalState.column;
            operatorSelect.value = originalState.operator;
            valueInput.value = originalState.value;
            operatorSelect.disabled = !originalState.column;
            valueInput.disabled = !originalState.column;
          }
          filterRow.classList.remove("is-editing");
          originalState = null;
          this.applyAllFilters();
          this.validateAllFilters();
          el.blur();
        }
      });
    });

    // Operator change
    operatorSelect.addEventListener("change", () => {
      // setEditing() handled by focus
      this.validateAllFilters();
      this.applyAllFilters(); // Update immediately
    });

    // Value input
    valueInput.addEventListener("input", () => {
      // setEditing() handled by focus
      this.validateAllFilters();
      // Even though we mute while editing, we still want to validity checks
      this.applyAllFilters();
    });

    // Logic change
    logicRadios.forEach((radio) => {
      radio.addEventListener("change", () => {
        // Mute logic: trigger validation/application.
        // The actual muting happens in applyAllFilters().
        this.validateAllFilters();
        // Auto-apply to immediately show the "muted" effect
        this.applyAllFilters();
      });
    });

    // Enter key on value input - apply all filters
    valueInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const applyBtn = document.getElementById("applyFiltersBtn");
        if (applyBtn && !applyBtn.disabled) {
          // Simulate Apply Button Click: Remove editing state and Apply
          document
            .querySelectorAll(".is-editing")
            .forEach((el) => el.classList.remove("is-editing"));
          this.applyAllFilters();
          originalState = null; // Reset for this row (Apply commits state)
          valueInput.blur();
        }
      }
    });

    // Remove button click
    removeBtn.addEventListener("click", () => {
      const filterRows = document.getElementById("filterRows");

      // Find the connector that belongs to this row (the one right before it)
      let previousSibling = filterRow.previousElementSibling;
      if (
        previousSibling &&
        previousSibling.classList.contains("filter-logic-connector")
      ) {
        previousSibling.remove();
      }

      // Remove the filter row itself
      filterRow.remove();

      // Clean up: ensure first element is always a filter row, not a connector
      if (filterRows && filterRows.children.length > 0) {
        // Keep removing connectors from the start until we hit a filter row
        while (
          filterRows.children.length > 0 &&
          filterRows.children[0].classList.contains("filter-logic-connector")
        ) {
          filterRows.children[0].remove();
        }

        // Reset margin on the first filter row
        if (
          filterRows.children.length > 0 &&
          filterRows.children[0].classList.contains("filter-row-sidebar")
        ) {
          filterRows.children[0].style.marginTop = "0";
        }
      }

      // Check if all filter rows are gone - show empty state message
      const actualFilterRows = filterRows
        ? filterRows.querySelectorAll(".filter-row-sidebar")
        : [];
      if (actualFilterRows.length === 0 && filterRows) {
        filterRows.innerHTML =
          '<p class="empty-state-message" id="noFiltersMessage">No applied filters</p>';
      }

      // Update badge count
      this.updateFilterBadge(actualFilterRows.length);
      this.validateAllFilters();

      // AUTO-APPLY: Apply remaining filters immediately after removal
      this.applyAllFilters();
    });

    // Initial validation
    this.validateAllFilters();
  }

  /**
   * Validate all filters and enable/disable Apply button
   * Logic: Enable ONLY if filters are "Dirty" (Changed from applied state) or Valid New Filters exist.
   */
  validateAllFilters() {
    const filterRows = document.querySelectorAll(
      "#filterRows .filter-row-sidebar",
    );
    const applyBtn = document.getElementById("applyFiltersBtn");
    const clearBtn = document.getElementById("clearFiltersBtn");

    if (!applyBtn) return;

    // Manage Clear button state
    // Only enable if there are actually applied filters in the table
    if (clearBtn) {
      clearBtn.disabled =
        !Array.isArray(this.table.filters) || this.table.filters.length === 0;
    }

    let allValid = true;
    let isDirty = false;
    const appliedFilters = this.table.filters || [];

    // Check 1: Length mismatch (Added or Deleted rows)
    if (filterRows.length !== appliedFilters.length) {
      isDirty = true;
    }

    filterRows.forEach((row, index) => {
      const column = row.querySelector(".filter-column").value;
      const value = row.querySelector(".filter-value").value.trim();
      const operator = row.querySelector(".filter-operator").value;

      if (column && value) {
        // Valid
      } else {
        // Invalid
        allValid = false;
      }

      // Check 2: Content mismatch (Edited rows)
      // If dirty already detected via length, we still check validity
      // If length matches, we must check content
      if (!isDirty && index < appliedFilters.length) {
        const applied = appliedFilters[index];
        if (
          column !== applied.column ||
          operator !== applied.operator ||
          value !== applied.value
        ) {
          isDirty = true;
        }
      } else if (!isDirty && index >= appliedFilters.length) {
        // Should be covered by length check, but just in case
        if (column || value) isDirty = true; // New content
      }
    });

    // Add Button state
    const addFilterBtn = document.getElementById("addFilterBtn");
    if (addFilterBtn) {
      if (filterRows.length === 0) {
        addFilterBtn.disabled = false;
      } else {
        addFilterBtn.disabled = !allValid;
      }
    }

    // Apply Button State
    // Disabled if: No filters to apply OR No Changes (Clean) AND NOT Valid
    // User Logic: "Only enabled if new filter is added... or edited... and need to reapply"
    // Also: "disabled if there is no filters" -> Covered by isDirty (0 applied, 0 DOM -> Clean)
    // If 0 applied, 1 DOM -> Dirty -> Enabled.

    if (!isDirty) {
      applyBtn.disabled = true;
    } else {
      applyBtn.disabled = !allValid;
    }
  }

  /**
   * Apply all filters from sidebar.
   */
  applyAllFilters() {
    const filterRows = document.querySelectorAll(
      "#filterRows .filter-row-sidebar",
    );
    const filters = [];

    filterRows.forEach((row, index) => {
      const column = row.querySelector(".filter-column").value;
      const operator = row.querySelector(".filter-operator").value;
      const value = row.querySelector(".filter-value").value.trim();
      const isEditing = row.classList.contains("is-editing");

      // Get logic from the connector BEFORE this row (if it exists)
      let logic = "AND";
      if (index > 0) {
        // Logic radios are in the connector element before this row
        let previousSibling = row.previousElementSibling;
        if (
          previousSibling &&
          previousSibling.classList.contains("filter-logic-connector")
        ) {
          const logicChecked = previousSibling.querySelector(
            ".filter-logic-radio:checked",
          );
          if (logicChecked) {
            logic = logicChecked.value;
          }
        }
      }

      // Edit Mute: If row is being edited, treat it as incomplete (skip it)
      if (column && value && !isEditing) {
        // Chained Mute Logic:
        // We must check if THIS row is part of a consecutive OR chain that ends in an incomplete row.
        // If so, we mute this row.
        // Logic: Look ahead. If we find an OR connector leading to an incomplete row before the chain breaks (changes to AND or ends), mute.

        let muteThisRow = false;
        let lookAheadIndex = index;

        // Keep looking ahead as long as we have rows
        while (lookAheadIndex < filterRows.length - 1) {
          const nextRowElement = filterRows[lookAheadIndex + 1];

          // Check connector between current lookAhead and next
          // The connector is the PREVIOUS sibling of the NEXT row
          const connector = nextRowElement.previousElementSibling;
          let isOr = false;

          if (
            connector &&
            connector.classList.contains("filter-logic-connector")
          ) {
            const radio = connector.querySelector(
              ".filter-logic-radio:checked",
            );
            if (radio && radio.value === "OR") {
              isOr = true;
            }
          }

          if (!isOr) {
            // Chain broke (switched to AND or no connector).
            // Since we didn't find an incomplete row yet, this whole chain is valid.
            break;
          }

          // We are in an OR chain. Check if the next row is incomplete.
          const nextCol = nextRowElement.querySelector(".filter-column").value;
          const nextVal = nextRowElement.querySelector(".filter-value").value;
          // Check if next row is being edited
          const nextIsEditing = nextRowElement.classList.contains("is-editing");

          if (!nextCol || !nextVal || nextIsEditing) {
            // Found an incomplete (or editing) row at the end of this OR link.
            // Since we have been in an OR chain starting from 'index', we must mute 'index'.
            muteThisRow = true;
            break;
          }

          // Next row is valid, but it might be followed by another OR...
          lookAheadIndex++;
        }

        if (!muteThisRow) {
          // Standard logic application
          // Get logic from the connector BEFORE this row (to determine how to add to filters array)
          // ... (existing logic)
          // First filter doesn't have logic, subsequent filters use selected logic
          if (filters.length === 0) {
            filters.push({ column, operator, value });
          } else {
            filters.push({ logic, column, operator, value });
          }
        }
      }
    });

    // Update table filters (array format)
    this.table.filters = filters;
    this.table.currentPage = 1; // Reset to first page
    this.table.selectedConfigId = null; // Clear active view (config changed)
    // Keep lastLoadedConfigId so Update button stays enabled

    // Use updateTable instead of render to preserve sidebar state (filter rows)
    this.table.updateTable();
    this.table.saveTableState();

    // Update badge to show applied filters count
    this.updateFilterBadge(filters.length);

    // Update button states (specifically Clear button)
    this.validateAllFilters();

    // Refresh saved views to remove active highlight
    this.populateSavedViews();
  }

  /**
   * Clear all filters.
   */
  clearAllFilters() {
    const filterRows = document.getElementById("filterRows");
    if (filterRows) {
      filterRows.innerHTML =
        '<p class="empty-state-message" id="noFiltersMessage">No applied filters</p>';
    }
    this.table.filters = []; // Array format
    this.table.selectedConfigId = null; // Clear active view (config changed)
    // Keep lastLoadedConfigId so Update button stays enabled
    this.table.updateTable(); // Use updateTable instead of render
    this.table.saveTableState();
    this.updateFilterBadge(0);
    this.validateAllFilters(); // Update button states

    // Refresh saved views to remove active highlight
    this.populateSavedViews();
  }

  /**
   * Update filter badge count.
   * @param {number} count - The number of applied filters.
   */
  updateFilterBadge(count) {
    const badge = document.querySelector(
      '.sidebar-section[data-section="filters"] .badge',
    );
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? "inline-block" : "none";
    }
  }

  /**
   * Refresh all filter column dropdowns to reflect current column order/visibility.
   */
  refreshFilterDropdowns() {
    const filterRows = document.querySelectorAll(
      "#filterRows .filter-row-sidebar",
    );

    filterRows.forEach((row) => {
      const columnSelect = row.querySelector(".filter-column");
      if (!columnSelect) return;

      const currentValue = columnSelect.value;

      // Rebuild dropdown options
      const options = ['<option value="">Select Column</option>'];
      this.table.columnOrder.forEach((key) => {
        if (!this.table.hiddenColumns.has(key)) {
          const col = this.table.columns.find((c) => c.key === key);
          if (col) {
            const selected = col.key === currentValue ? "selected" : "";
            options.push(
              `<option value="${col.key}" ${selected}>${col.label}</option>`,
            );
          }
        }
      });

      columnSelect.innerHTML = options.join("");
    });
  }

  /**
   * Populate column manager in sidebar.
   */
  populateColumns() {
    const columnList = document.getElementById("columnList");
    if (!columnList) return;

    columnList.innerHTML = "";
    this.table.columnOrder.forEach((key) => {
      const col = this.table.columns.find((c) => c.key === key);
      if (!col) return;

      const isVisible = !this.table.hiddenColumns.has(key);

      const listItem = document.createElement("li");
      listItem.className = "column-item";
      listItem.dataset.column = key;
      listItem.draggable = true;
      listItem.innerHTML = `
                <input type="checkbox" ${isVisible ? "checked" : ""}>
                <span>${col.label}</span>
                <i class="fas fa-grip-vertical drag-handle"></i>
            `;

      // Add Enter key support for checkbox
      const checkbox = listItem.querySelector('input[type="checkbox"]');
      checkbox.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          checkbox.checked = !checkbox.checked;
        }
      });

      // Drag and drop event listeners
      listItem.addEventListener("dragstart", (e) => {
        listItem.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", key);
      });

      listItem.addEventListener("dragend", () => {
        listItem.classList.remove("dragging");
      });

      listItem.addEventListener("dragover", (e) => {
        e.preventDefault();
        const dragging = columnList.querySelector(".dragging");
        const afterElement = this.getDragAfterElement(columnList, e.clientY);

        if (afterElement == null) {
          columnList.appendChild(dragging);
        } else {
          columnList.insertBefore(dragging, afterElement);
        }
      });

      columnList.appendChild(listItem);
    });
  }

  /**
   * Get element after drag position (for drag and drop).
   * @param {HTMLElement} container - The container element.
   * @param {number} y - The y coordinate of the mouse cursor.
   * @returns {HTMLElement} The element after the drag position.
   */
  getDragAfterElement(container, y) {
    const draggableElements = [
      ...container.querySelectorAll(".column-item:not(.dragging)"),
    ];

    return draggableElements.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
          return { offset: offset, element: child };
        } else {
          return closest;
        }
      },
      { offset: Number.NEGATIVE_INFINITY },
    ).element;
  }

  /**
   * Apply column changes from sidebar.
   */
  applyColumnChanges() {
    const columnList = document.getElementById("columnList");
    if (!columnList) return;

    // Get new column order from DOM
    const newOrder = Array.from(
      columnList.querySelectorAll(".column-item"),
    ).map((item) => item.dataset.column);

    // Get hidden columns
    const newHiddenColumns = new Set();
    columnList.querySelectorAll(".column-item").forEach((item) => {
      const checkbox = item.querySelector('input[type="checkbox"]');
      if (!checkbox.checked) {
        newHiddenColumns.add(item.dataset.column);
      }
    });

    // Update table state
    this.table.columnOrder = newOrder;
    this.table.hiddenColumns = newHiddenColumns;
    this.table.selectedConfigId = null; // Clear active view (config changed)
    // Keep lastLoadedConfigId so Update button stays enabled

    // Update table
    this.table.updateTable();
    this.table.saveTableState();

    // Refresh filter dropdowns to reflect new column order/visibility
    this.refreshFilterDropdowns();

    // Refresh saved views to remove active highlight
    this.populateSavedViews();
  }

  /**
   * Reset columns to default state.
   */
  resetColumns() {
    // Reset to original column order and make all visible
    this.table.columnOrder = [...this.table.defaultState.columnOrder];
    this.table.hiddenColumns = new Set();
    this.table.selectedConfigId = null;
    this.table.lastLoadedConfigId = null; // Reset completely on full reset

    // Repopulate column list
    this.populateColumns();

    // Update table
    this.table.updateTable();
    this.table.saveTableState();

    // Refresh filter dropdowns to reflect reset columns
    this.refreshFilterDropdowns();

    // Refresh saved views to remove active highlight
    this.populateSavedViews();
  }

  /**
   * Populate saved views in sidebar.
   */
  populateSavedViews() {
    const viewsList = document.getElementById("savedViewsList");
    const updateBtn = document.getElementById("updateViewBtn");

    if (!viewsList) return;

    viewsList.innerHTML = "";

    if (
      !Array.isArray(this.table.savedConfigs) ||
      this.table.savedConfigs.length === 0
    ) {
      viewsList.innerHTML = '<p class="empty-state-message">No saved views</p>';
      if (updateBtn) updateBtn.disabled = true;
      return;
    }

    // Separate own configs and shared configs
    const currentUserId =
      window.currentUser?.id || parseInt(sessionStorage.getItem("user_id"), 10);
    const ownConfigs = this.table.savedConfigs.filter(
      (c) => c.user_id === currentUserId,
    );
    const sharedConfigs = this.table.savedConfigs.filter(
      (c) => c.user_id !== currentUserId,
    );

    const renderConfigGroup = (configs, title) => {
      if (configs.length === 0) return "";

      const groupHeader = document.createElement("div");
      groupHeader.className = "sidebar-group-header";
      groupHeader.style.cssText =
        "font-size: 0.7rem; text-transform: uppercase; color: #6c757d; margin: 10px 0 5px 0; font-weight: bold;";
      groupHeader.textContent = title;
      viewsList.appendChild(groupHeader);

      configs.forEach((config) => {
        const viewItem = document.createElement("div");
        viewItem.className = "saved-view-item";
        viewItem.dataset.configId = config.id;

        // Highlight active view (current configuration)
        const isActive = config.id === this.table.selectedConfigId;
        if (isActive) {
          viewItem.classList.add("active");
        }

        const displayName =
          config.config_name.length > 25
            ? config.config_name.substring(0, 24) + "…"
            : config.config_name;

        const isOwner = config.user_id === currentUserId;

        viewItem.innerHTML = `
                <div class="view-info" style="cursor: pointer; flex: 1;">
                    <div style="display: flex; flex-direction: column;">
                        <span class="view-name" title="${
                          config.config_name
                        }">${displayName}</span>
                        ${
                          config.notes
                            ? `<small class="text-muted" style="font-size: 0.7rem;">${config.notes}</small>`
                            : ""
                        }
                    </div>
                    ${
                      config.is_default
                        ? '<span class="badge badge-primary badge-sm">Default</span>'
                        : ""
                    }
                </div>
                <div class="view-actions">
                    ${
                      isOwner
                        ? `
                        <button class="btn btn-sm btn-link share-view-btn" title="Share this view">
                            <i class="fas fa-share-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-link set-default-btn" title="${
                          config.is_default ? "Remove default" : "Set as default"
                        }">
                            <i class="fas fa-star${
                              config.is_default ? " text-warning" : ""
                            }"></i>
                        </button>
                        <button class="btn btn-sm btn-link delete-view-btn" title="Delete this view">
                            <i class="fas fa-trash text-danger"></i>
                        </button>
                    `
                        : ""
                    }
                </div>
            `;

        // Click on view info to load it
        const viewInfo = viewItem.querySelector(".view-info");
        if (viewInfo) {
          viewInfo.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.loadView(config);
          });
        }

        if (isOwner) {
          // Share button
          viewItem
            .querySelector(".share-view-btn")
            .addEventListener("click", (e) => {
              e.stopPropagation();
              this.shareView(config);
            });

          // Set/Remove default button
          viewItem
            .querySelector(".set-default-btn")
            .addEventListener("click", (e) => {
              e.stopPropagation();
              if (config.is_default) {
                this.removeDefaultView(config.id);
              } else {
                this.setDefaultView(config.id);
              }
            });

          // Delete button
          viewItem
            .querySelector(".delete-view-btn")
            .addEventListener("click", (e) => {
              e.stopPropagation();
              this.deleteView(config);
            });
        }

        viewsList.appendChild(viewItem);
      });
    };

    renderConfigGroup(ownConfigs, "My Views");
    renderConfigGroup(sharedConfigs, "Shared with Me");

    // Update button: Enable if there's a last loaded view (even if not currently active)
    if (updateBtn) {
      if (this.table.lastLoadedConfigId) {
        const lastLoadedConfig = this.table.savedConfigs.find(
          (c) => c.id === this.table.lastLoadedConfigId,
        );
        if (lastLoadedConfig) {
          updateBtn.disabled = false;
          // Show view name in button (truncated if needed)
          const displayName =
            lastLoadedConfig.config_name.length > 15
              ? lastLoadedConfig.config_name.substring(0, 14) + "…"
              : lastLoadedConfig.config_name;
          updateBtn.innerHTML = `<i class="fas fa-sync"></i> Update "${displayName}"`;
          updateBtn.title = `Update "${lastLoadedConfig.config_name}" with current settings`;
        } else {
          updateBtn.disabled = true;
          updateBtn.innerHTML = '<i class="fas fa-sync"></i> Update';
          updateBtn.title = "Load a view to enable update";
        }
      } else {
        updateBtn.disabled = true;
        updateBtn.innerHTML = '<i class="fas fa-sync"></i> Update';
        updateBtn.title = "Load a view to enable update";
      }
    }
  }

  /**
   * Save current view configuration.
   */
  saveView() {
    // Use showInputModal instead of prompt
    this.showInputModal("Enter configuration name:", (name) => {
      if (!name || !name.trim()) return;
      this.saveViewWithName(name.trim());
    });
  }

  /**
   * Save view with a specific name.
   * @param {string} name - The name of the view configuration.
   */
  saveViewWithName(name) {
    const duplicate = this.table.savedConfigs.find(
      (c) => c.config_name.toLowerCase() === name.trim().toLowerCase(),
    );
    if (duplicate) {
      ToastNotification.error(
        `Configuration name "${name.trim()}" already exists.Please choose a different name.`,
      );
      return;
    }

    const config = {
      config_name: name.trim(),
      column_order: JSON.stringify(this.table.columnOrder),
      hidden_columns: JSON.stringify(Array.from(this.table.hiddenColumns)),
      filters: JSON.stringify(this.table.filters),
      sort_config: JSON.stringify(this.table.currentSort),
      is_default: false,
    };

    // Get button and show loading state
    const saveBtn = document.getElementById("saveViewBtn");
    const loadingState = this.table.showButtonLoading(saveBtn, "Saving...");

    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    this.table
      .fetchWithRetry("/api/table-config/" + this.table.pageName, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(config),
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} `);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          ToastNotification.success(
            `View "${name.trim()}" saved successfully!`,
          );

          // Set this newly saved view as both selected and last loaded
          this.table.selectedConfigId = data.id;
          this.table.lastLoadedConfigId = data.id;

          // Reload configurations WITHOUT applying default
          // Just refresh the list
          this.table
            .fetchWithRetry("/api/table-config/" + this.table.pageName)
            .then((response) => response.json())
            .then((configs) => {
              this.table.savedConfigs = configs || [];
              this.populateSavedViews();
            });
        } else {
          ToastNotification.error(
            "Failed to save configuration: " + (data.error || "Unknown error"),
          );
        }
      })
      .catch((error) => {
        if (error.message === "Max retries exceeded") {
          console.error(
            "Failed to save configuration after multiple retries:",
            error,
          );
          ToastNotification.error(
            "Unable to save view. Please check your connection and try again.",
          );
        } else {
          console.error("Error saving configuration:", error);
          ToastNotification.error(
            "Error saving configuration: " + error.message,
          );
        }
      })
      .finally(() => {
        // Restore button state
        loadingState.restore();
      });
  }

  /**
   * Update the currently active saved view with current table state.
   */
  updateView() {
    if (!this.table.lastLoadedConfigId) {
      ToastNotification.warning(
        "No view selected. Please load a view first or create a new one.",
      );
      return;
    }

    const currentConfig = this.table.savedConfigs.find(
      (c) => c.id === this.table.lastLoadedConfigId,
    );
    if (!currentConfig) {
      ToastNotification.error("Selected view not found.");
      return;
    }

    // Use generic confirm modal instead of delete modal
    showConfirmModal(
      `Update view "${currentConfig.config_name}" with current settings?`,
      () => {
        this.performViewUpdate(currentConfig);
      },
    );
  }

  /**
   * Perform the view update operation.
   * @param {Object} currentConfig - The current configuration object.
   */
  performViewUpdate(currentConfig) {
    const config = {
      column_order: JSON.stringify(this.table.columnOrder),
      hidden_columns: JSON.stringify(Array.from(this.table.hiddenColumns)),
      filters: JSON.stringify(this.table.filters),
      sort_config: JSON.stringify(this.table.currentSort),
    };

    // Get button and show loading state
    const updateBtn = document.getElementById("updateViewBtn");
    const loadingState = this.table.showButtonLoading(updateBtn, "Updating...");

    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    this.table
      .fetchWithRetry(`/api/table-config/${this.table.lastLoadedConfigId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(config),
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} `);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          ToastNotification.success(
            `View "${currentConfig.config_name}" updated successfully!`,
          );

          // After update, the current state now matches the saved view
          this.table.selectedConfigId = this.table.lastLoadedConfigId;

          // Reload configurations to refresh the list
          this.table
            .fetchWithRetry("/api/table-config/" + this.table.pageName)
            .then((response) => response.json())
            .then((configs) => {
              this.table.savedConfigs = configs || [];
              this.populateSavedViews();
            });
        } else {
          ToastNotification.error(
            "Failed to update configuration: " +
              (data.error || "Unknown error"),
          );
        }
      })
      .catch((error) => {
        if (error.message === "Max retries exceeded") {
          console.error(
            "Failed to update configuration after multiple retries:",
            error,
          );
          ToastNotification.error(
            "Unable to update view. Please check your connection and try again.",
          );
        } else {
          console.error("Error updating configuration:", error);
          ToastNotification.error(
            "Error updating configuration: " + error.message,
          );
        }
      })
      .finally(() => {
        // Restore button state
        loadingState.restore();
      });
  }

  /**
   * Delete selected view.
   * @param {Object} config - The configuration object to delete.
   */
  deleteView(config) {
    if (!config) return;

    // Use showDeleteConfirm modal instead of confirm
    showDeleteConfirm(
      null,
      `Are you sure you want to delete the view "${config.config_name}"?`,
      () => {
        this.performViewDelete(config);
      },
    );
  }

  /**
   * Perform the view delete operation.
   * @param {Object} config - The configuration object to delete.
   */
  performViewDelete(config) {
    // Find the delete button for this specific view
    const viewItem = document.querySelector(
      `.saved-view-item[data-config-id="${config.id}"]`,
    );
    const deleteBtn = viewItem
      ? viewItem.querySelector(".delete-view-btn")
      : null;
    const loadingState = deleteBtn
      ? this.table.showButtonLoading(deleteBtn, "")
      : null;

    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    this.table
      .fetchWithRetry(`/api/table-config/${config.id}`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} `);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          ToastNotification.success(
            `View "${config.config_name}" deleted successfully!`,
          );

          // If deleted view was active or last loaded, clear those IDs
          if (this.table.selectedConfigId === config.id) {
            this.table.selectedConfigId = null;
          }
          if (this.table.lastLoadedConfigId === config.id) {
            this.table.lastLoadedConfigId = null;
          }
          // Reload configurations and refresh sidebar
          this.table.loadConfiguration();
        } else {
          ToastNotification.error(
            "Failed to delete configuration: " +
              (data.error || "Unknown error"),
          );
        }
      })
      .catch((error) => {
        if (error.message === "Max retries exceeded") {
          console.error(
            "Failed to delete configuration after multiple retries:",
            error,
          );
          ToastNotification.error(
            "Unable to delete view. Please check your connection and try again.",
          );
        } else {
          console.error("Error deleting configuration:", error);
          ToastNotification.error(
            "Error deleting configuration: " + error.message,
          );
        }
      })
      .finally(() => {
        // Restore button state
        if (loadingState) {
          loadingState.restore();
        }
      });
  }

  /**
   * Load a view configuration.
   * @param {Object} config - The configuration object to load.
   */
  loadView(config) {
    this.table.applyConfiguration(config);
    this.table.selectedConfigId = config.id; // Active view (matches exactly)
    this.table.lastLoadedConfigId = config.id; // Last loaded (for Update button)

    // Refresh all sidebar sections to reflect loaded state
    this.loadExistingFilters();
    this.populateColumns();
    this.populateSavedViews();
  }

  /**
   * Set a view as default.
   * @param {string|number} configId - The ID of the configuration to set as default.
   */
  setDefaultView(configId) {
    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    fetch(`/api/table-config/${this.table.pageName}/${configId}/set-default`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} `);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Just reload the configs list WITHOUT applying the default
          fetch("/api/table-config/" + this.table.pageName)
            .then((response) => response.json())
            .then((configs) => {
              this.table.savedConfigs = configs || [];
              this.populateSavedViews();
            });
        } else {
          ToastNotification.error(
            "Failed to set default configuration: " +
              (data.error || "Unknown error"),
          );
        }
      })
      .catch((error) => {
        console.error("Error setting default configuration:", error);
        ToastNotification.error(
          "Error setting default configuration: " + error.message,
        );
      });
  }

  /**
   * Remove default status from a view.
   * @param {string|number} configId - The ID of the configuration to remove default status from.
   */
  removeDefaultView(configId) {
    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    fetch(
      `/api/table-config/${this.table.pageName}/${configId}/remove-default`,
      {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} `);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Just reload the configs list WITHOUT applying anything
          fetch("/api/table-config/" + this.table.pageName)
            .then((response) => response.json())
            .then((configs) => {
              this.table.savedConfigs = configs || [];
              this.populateSavedViews();
            });
        } else {
          ToastNotification.error(
            "Failed to remove default configuration: " +
              (data.error || "Unknown error"),
          );
        }
      })
      .catch((error) => {
        console.error("Error removing default configuration:", error);
        ToastNotification.error(
          "Error removing default configuration: " + error.message,
        );
      });
  }

  /**
   * Restore filter UI from saved state.
   */
  restoreFilterUI() {
    if (!this.table.filters || this.table.filters.length === 0) {
      return;
    }

    const filterRows = document.getElementById("filterRows");
    if (!filterRows) return;

    // Clear existing empty state message
    filterRows.innerHTML = "";

    // Rebuild filter rows from saved state
    this.table.filters.forEach((filter, index) => {
      this.addFilterRow(filter.column, filter.operator, filter.value);

      // Set logic for subsequent filters
      if (index > 0 && filter.logic) {
        const filterRow = filterRows.children[filterRows.children.length - 1];
        const logicConnector = filterRow.previousElementSibling;
        if (
          logicConnector &&
          logicConnector.classList.contains("filter-logic-connector")
        ) {
          const logicRadio = logicConnector.querySelector(
            `input[value = "${filter.logic}"]`,
          );
          if (logicRadio) {
            logicRadio.checked = true;
          }
        }
      }
    });

    // Update filter badge
    this.updateFilterBadge(this.table.filters.length);
  }

  /**
   * Share a view configuration.
   * @param {Object} config - The configuration object to share.
   */
  shareView(config) {
    const userId = prompt("Enter User ID to share with:");
    if (!userId) return;

    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    fetch(`/api/table-config/${config.id}/share`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ user_ids: [parseInt(userId, 10)] }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          ToastNotification.success(`Shared view "${config.config_name}"`);
        } else {
          ToastNotification.error("Failed to share view");
        }
      });
  }

  /**
   * Start polling for collaboration features (active filters).
   */
  startCollaborationPolling() {
    // Poll every 10 seconds
    this.collaborationInterval = setInterval(
      () => this.pollActiveFilters(),
      10000,
    );
    // Initial poll
    this.pollActiveFilters();
  }

  /**
   * Poll for active filters from other users.
   */
  pollActiveFilters() {
    // 1. Send current filters
    const csrfToken = document
      .querySelector("meta[name=csrf-token]")
      ?.getAttribute("content");
    fetch(`/api/active-filters/${this.table.pageName}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ filters: this.table.filters }),
    }).catch((e) => console.warn("Collaboration: Update failed", e));

    // 2. Fetch other users' filters
    fetch(`/api/active-filters/${this.table.pageName}`)
      .then((r) => r.json())
      .then((users) => {
        this.updateActiveUsersList(users);
      })
      .catch((e) => console.warn("Collaboration: Fetch failed", e));
  }

  /**
   * Update the UI with the list of active users and their filters.
   * @param {Array} users - The list of active users.
   */
  updateActiveUsersList(users) {
    const list = document.getElementById("activeUsersList");
    if (!list) return;

    if (!users || users.length === 0) {
      list.innerHTML =
        '<p class="empty-state-message">No other users active on this page</p>';
      return;
    }

    list.innerHTML = "";
    users.forEach((u) => {
      const userItem = document.createElement("div");
      userItem.className = "active-user-item";
      userItem.style.cssText = "margin-bottom: 8px; padding: 5px;";

      let filterSummary = "No active filters";
      try {
        const filters = JSON.parse(u.filter_data);
        if (filters && filters.length > 0) {
          filterSummary = filters
            .map((f) => `${f.column} ${f.operator} "${f.value}"`)
            .join(", ");
        }
      } catch (e) {
        // Ignore parse error
      }

      userItem.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="fas fa-circle" style="color: #28a745; font-size: 0.6rem;"></i>
                    <strong style="font-size: 0.85rem;">${u.username}</strong>
                </div>
                <div style="font-size: 0.7rem; color: #6c757d; padding-left: 16px;">
                    Filtering: ${filterSummary}
                </div>
            `;
      list.appendChild(userItem);
    });
  }

  /**
   * Show input modal helper (replacement for prompt).
   * @param {string} message - The modal message/label.
   * @param {Function} callback - The callback function to run with the input value.
   */
  showInputModal(message, callback) {
    if (typeof window.showInputModal === "function") {
      window.showInputModal(message, callback);
    }
  }
}

// Export for use in advanced-table.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = TableSidebar;
}
