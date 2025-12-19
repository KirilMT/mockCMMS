/**
 * Column Resizing for Advanced Table
 * Allows users to resize table columns by dragging
 */

/**
 * Initialize column resizing
 */
AdvancedTable.prototype.initColumnResize = function () {
  const table = this.container.querySelector(".advanced-table");
  if (!table) return;

  // Ensure table uses table-layout: fixed for predictable column widths
  if (table.style.tableLayout !== "fixed") {
    table.style.tableLayout = "fixed";
  }

  // EXCEL-LIKE BEHAVIOR:
  // 1. Lock table width to current pixel value to disconnect from percentage
  // 2. Lock all column widths to current pixel values to prevent auto-layout shifting

  // Set initial table width in pixels using precise float values
  if (!table.style.width || table.style.width.includes("%")) {
    table.style.width = table.getBoundingClientRect().width + "px";
  }

  const headers = table.querySelectorAll("th.sortable");

  // Initialize all columns with explicit pixel widths
  // Initialize all columns with explicit pixel widths
  headers.forEach((th) => {
    if (!th.style.width) {
      // Bug #8: Apply smart default widths based on column content
      const columnKey = th.dataset.column;
      let defaultWidth = 0;

      if (columnKey) {
        const key = columnKey.toLowerCase();
        if (key.includes("id")) defaultWidth = 65;
        else if (key.includes("code")) defaultWidth = 150;
        else if (
          key.includes("description") ||
          key.includes("desc") ||
          key.includes("summary")
        )
          defaultWidth = 350;
        else if (
          key.includes("name") ||
          key.includes("title") ||
          key.includes("subject")
        )
          defaultWidth = 250;
        else if (
          key.includes("status") ||
          key.includes("state") ||
          key.includes("type")
        )
          defaultWidth = 140;
        else if (
          key.includes("date") ||
          key.includes("time") ||
          key.includes("created") ||
          key.includes("updated")
        )
          defaultWidth = 160;
        else if (
          key.includes("email") ||
          key.includes("user") ||
          key.includes("assignee")
        )
          defaultWidth = 200;
        else defaultWidth = 150; // General default
      }

      // If we have a smart default, use it directly. Otherwise use computed width
      const computedWidth = th.getBoundingClientRect().width;
      th.style.width = (defaultWidth > 0 ? defaultWidth : computedWidth) + "px";
    }

    // Remove existing resize handle if present
    const existingHandle = th.querySelector(".resize-handle");
    if (existingHandle) {
      existingHandle.remove();
    }

    // Create resize handle
    const resizeHandle = document.createElement("div");
    resizeHandle.className = "resize-handle";
    th.appendChild(resizeHandle);

    let startX = 0;
    let startWidth = 0;
    let startTableWidth = 0;
    let isResizing = false;
    let hasMoved = false;
    let animationFrameId = null;

    // Flag to suppress click event (sorting) after resize
    let justResized = false;

    // Add capture-phase click listener to header to prevent sorting if we just resized
    th.addEventListener(
      "click",
      (e) => {
        if (justResized) {
          e.preventDefault();
          e.stopPropagation();
          // Reset flag immediately after catching the event
          justResized = false;
        }
      },
      true,
    ); // Capture phase

    resizeHandle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      e.stopPropagation();

      isResizing = true;
      hasMoved = false;
      startX = e.pageX;

      // Use getBoundingClientRect for sub-pixel precision to prevent jitter
      startWidth = th.getBoundingClientRect().width;
      startTableWidth = table.getBoundingClientRect().width;

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      const onMouseMove = (e) => {
        if (!isResizing) return;

        // Use requestAnimationFrame for smooth rendering
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId);
        }

        animationFrameId = requestAnimationFrame(() => {
          const diff = e.pageX - startX;

          if (Math.abs(diff) > 2) {
            hasMoved = true;
            const newWidth = Math.max(50, startWidth + diff);

            // Update column width
            th.style.width = newWidth + "px";
            th.style.minWidth = newWidth + "px";
            th.style.maxWidth = newWidth + "px";

            // Update table width synchronously
            // We recalculate widthChange based on the actual newWidth applied (which might be clamped by min 50px)
            const actualWidthChange = newWidth - startWidth;
            table.style.width = startTableWidth + actualWidthChange + "px";
          }
        });
      };

      const onMouseUp = () => {
        isResizing = false;
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId);
        }

        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";

        if (hasMoved) {
          this.saveColumnWidths();
          // Set flag to suppress subsequent click event
          justResized = true;
          // Clear flag after a short delay just in case click doesn't fire
          setTimeout(() => {
            justResized = false;
          }, 100);
        }
      };

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    });

    // Prevent click on handle from triggering sort
    resizeHandle.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
    });

    // Add double-click to auto-fit column
    resizeHandle.addEventListener("dblclick", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const table = th.closest("table");
      const columnIndex = Array.from(th.parentNode.children).indexOf(th);

      function measureContentWidth(text, refElem) {
        const measurer = document.createElement("span");
        measurer.style.visibility = "hidden";
        measurer.style.position = "absolute";
        measurer.style.whiteSpace = "nowrap";
        measurer.style.font = window.getComputedStyle(refElem).font;
        measurer.style.fontWeight = window.getComputedStyle(refElem).fontWeight;
        measurer.style.fontSize = window.getComputedStyle(refElem).fontSize;
        measurer.style.padding = window.getComputedStyle(refElem).padding;
        measurer.textContent = text;
        document.body.appendChild(measurer);
        const width = measurer.getBoundingClientRect().width; // Use float width
        document.body.removeChild(measurer);
        return width;
      }

      // Measure header
      let maxWidth = measureContentWidth(th.textContent, th);

      // Measure all cells in column
      const rows = table.querySelectorAll("tbody tr");
      rows.forEach((row) => {
        const cell = row.children[columnIndex];
        if (cell) {
          maxWidth = Math.max(
            maxWidth,
            measureContentWidth(cell.textContent, cell),
          );
        }
      });

      // Add a small buffer for sort icon, etc.
      // Reduced buffer from 24 to 12 as requested
      let finalWidth = Math.max(50, Math.min(3000, Math.ceil(maxWidth) + 5));

      // Calculate width difference using current float width
      const currentWidth = th.getBoundingClientRect().width;
      const widthDiff = finalWidth - currentWidth;

      // Set width for only the target column
      th.style.width = finalWidth + "px";
      th.style.minWidth = finalWidth + "px";
      th.style.maxWidth = finalWidth + "px";

      // Update table width to accommodate the auto-fit
      const currentTableWidth = table.getBoundingClientRect().width;
      table.style.width = currentTableWidth + widthDiff + "px";

      // Save all column widths
      this.saveColumnWidths();
    });
  });

  // Restore column widths from localStorage
  this.restoreColumnWidths();
};

/**
 * Save column widths to localStorage
 */
AdvancedTable.prototype.saveColumnWidths = function () {
  const table = this.container.querySelector(".advanced-table");
  if (!table) return;

  const widths = {};
  const headers = table.querySelectorAll("th.sortable");

  headers.forEach((th) => {
    const column = th.dataset.column;
    const width = th.style.width;
    if (column && width) {
      widths[column] = width;
    }
  });

  const storageKey = `table-column-widths-${this.pageName}`;
  localStorage.setItem(storageKey, JSON.stringify(widths));
};

/**
 * Restore column widths from localStorage
 */
AdvancedTable.prototype.restoreColumnWidths = function () {
  const storageKey = `table-column-widths-${this.pageName}`;
  const savedWidths = localStorage.getItem(storageKey);

  if (!savedWidths) return;

  try {
    const widths = JSON.parse(savedWidths);
    const table = this.container.querySelector(".advanced-table");
    if (!table) return;

    const headers = table.querySelectorAll("th.sortable");
    headers.forEach((th) => {
      const column = th.dataset.column;
      if (column && widths[column]) {
        th.style.width = widths[column];
        th.style.minWidth = widths[column];
        th.style.maxWidth = widths[column];
      }
    });
  } catch (error) {
    console.error("Error restoring column widths:", error);
  }
};

/**
 * Handle window resize events
 * Adjusts table width to fill container if needed
 */
AdvancedTable.prototype.handleWindowResize = function () {
  const table = this.container.querySelector(".advanced-table");
  const wrapper = this.container.querySelector(".advanced-table-wrapper");

  if (!table || !wrapper) return;

  // Get available width from wrapper (minus padding if any)
  const availableWidth = wrapper.clientWidth;
  const currentTableWidth = table.getBoundingClientRect().width;

  // If table is smaller than available width, expand it
  // Use a small buffer (5px) to avoid jitter
  if (currentTableWidth < availableWidth - 5) {
    table.style.width = availableWidth + "px";
  }
};

// Initialize resize listener
AdvancedTable.prototype.initResizeListener = function () {
  window.addEventListener("resize", () => {
    // Debounce resize
    if (this.resizeTimeout) clearTimeout(this.resizeTimeout);
    this.resizeTimeout = setTimeout(() => {
      this.handleWindowResize();
    }, 100);
  });

  // Initial check
  setTimeout(() => {
    this.handleWindowResize();
  }, 500); // Wait for initial render/layout
};
