import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f8fafc", // Clean light background
        surface: "#ffffff",    // Crisp white card surface
        border: {
          DEFAULT: "#e2e8f0",  // Light gray border
          subtle: "#f1f5f9",
          focus: "#2563eb",
        },
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",      // Restrained Blue Accent
          700: "#1d4ed8",
        },
        typography: {
          primary: "#0f172a",  // Dark charcoal
          secondary: "#475569",
          muted: "#64748b",
          light: "#94a3b8",
        },
        status: {
          success: "#059669",
          successBg: "#ecfdf5",
          warning: "#d97706",
          warningBg: "#fffbeb",
          error: "#dc2626",
          errorBg: "#fef2f2",
          info: "#2563eb",
          infoBg: "#eff6ff",
        },
      },
      borderRadius: {
        sm: "0.25rem",
        DEFAULT: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px 0 rgba(0, 0, 0, 0.04)",
        elevated: "0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;