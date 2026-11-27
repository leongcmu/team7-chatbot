import { defineConfig } from "vite";
export default defineConfig({
  build: {
    lib: {
      entry: "src/index.ts",
      formats: ["es"],
      fileName: "index",
      cssFileName: "chatbot",
    },
    rollupOptions: {
      output: { banner: '"use client";' },
      onwarn(warning, warn) {
        if (warning.code !== "MODULE_LEVEL_DIRECTIVE") warn(warning);
      },
      external: ["react", "react-dom", "react/jsx-runtime"],
    },
  },
  test: { environment: "jsdom", pool: "forks", maxWorkers: 1 },
});
