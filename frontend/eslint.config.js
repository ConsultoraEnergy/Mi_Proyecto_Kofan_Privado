import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";

export default [
  { ignores: ["dist/**", "coverage/**", "playwright-report/**", "test-results/**", "doc_frontend.py"] },
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  {
    files: ["**/*.{js,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser },
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrors: "none" }],
      // Vistas de página con nombre de una palabra (Home, Login...) son intencionales.
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "error",
      eqeqeq: ["error", "always", { null: "ignore" }],
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
  {
    files: ["tests/**/*.js", "e2e/**/*.js", "*.config.js"],
    languageOptions: { globals: { ...globals.node } },
  },
  // Debe ir al final: desactiva las reglas de estilo que Prettier ya controla.
  prettier,
];
