import { defineConfig } from "@playwright/test";

// The backend is mocked with page.route, so the frontend points at a fake API origin.
export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  use: { baseURL: "http://localhost:5174", channel: process.env.CI ? undefined : "chrome", viewport: { width: 1280, height: 900 } },
  webServer: { command: "npx vite --port 5174 --strictPort", url: "http://localhost:5174", reuseExistingServer: false,
               env: { VITE_API_URL: "http://api.test" }, timeout: 60_000 },
});
