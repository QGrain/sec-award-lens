import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_ACTIONS
    ? `/${process.env.GITHUB_REPOSITORY?.split("/")[1] ?? "sec-award-lens"}/`
    : "/",
  test: {
    environment: "node",
  },
});
