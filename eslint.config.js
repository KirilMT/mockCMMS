const globals = require("globals");
const js = require("@eslint/js");

module.exports = [
  js.configs.recommended,
  {
    ignores: ["**/apps/planning/src/static/js/manage_*.js"],
  },
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
        TableSidebar: "readonly",
        AdvancedTable: "writable",
        ToastNotification: "readonly",
        showConfirmModal: "readonly",
        showDeleteConfirm: "readonly",
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-undef": "error",
    },
  },
];
