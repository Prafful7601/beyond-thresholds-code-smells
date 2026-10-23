/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: { provider: "v8", reporter: ["text", "json-summary"], include: ["src/**/*.{ts,tsx}"],
                exclude: ["src/main.tsx", "src/test/**", "src/**/*.test.{ts,tsx}"] },
  },
});
