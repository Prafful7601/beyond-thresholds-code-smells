/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#0b0b0b", 2: "#52514e", 3: "#8a8984" },
        surface: { DEFAULT: "#fcfcfb", 2: "#f4f3f0", 3: "#e9e8e4" },
        brand: { DEFAULT: "#2a78d6", dark: "#1c5cab", light: "#e8f1fc" },
        clean: "#1baf7a",
        borderline: "#eb6834",
        clear: "#c0392b",
      },
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
                     mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
};
