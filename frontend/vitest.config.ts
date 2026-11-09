import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Test dei componenti (RT-09): jsdom, Testing Library, MSW. I test end-to-end
// stanno in e2e/ e li lancia Playwright (npm run test:e2e), non Vitest.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
  },
});
