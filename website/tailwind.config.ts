import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "on-secondary-container": "#b7b4b7",
        "on-secondary": "#303032",
        "on-secondary-fixed": "#1b1b1d",
        "on-tertiary-fixed": "#001b3c",
        "rating-gold": "#F5C518",
        "tertiary-fixed-dim": "#a7c8ff",
        "surface-container-low": "#2a1614",
        "on-primary": "#690003",
        "surface-bright": "#4a3330",
        "outline-variant": "#5e3f3b",
        "error": "#ffb4ab",
        "surface-variant": "#462f2c",
        "surface-container-high": "#3a2522",
        "surface-tint": "#ffb4aa",
        "secondary-fixed": "#e5e1e4",
        "on-surface": "#ffdad5",
        "tertiary-container": "#0072d7",
        "background": "#200e0c",
        "surface-dim": "#200e0c",
        "primary": "#ffb4aa",
        "on-tertiary-fixed-variant": "#004689",
        "secondary-fixed-dim": "#c8c6c8",
        "outline": "#af8782",
        "primary-fixed-dim": "#ffb4aa",
        "background-obsidian": "#09090B",
        "secondary": "#c8c6c8",
        "primary-container": "#e50914",
        "on-surface-variant": "#e9bcb6",
        "on-primary-fixed": "#410001",
        "on-secondary-fixed-variant": "#474649",
        "on-error-container": "#ffdad6",
        "tertiary": "#a7c8ff",
        "inverse-primary": "#c0000c",
        "inverse-on-surface": "#412b28",
        "on-primary-container": "#fff7f6",
        "surface-container-lowest": "#1a0908",
        "surface-container": "#2e1a18",
        "primary-fixed": "#ffdad5",
        "inverse-surface": "#ffdad5",
        "on-tertiary-container": "#f8f9ff",
        "surface-container-highest": "#462f2c",
        "secondary-container": "#474649",
        "on-error": "#690005",
        "error-container": "#93000a",
        "text-secondary": "#A1A1AA",
        "text-primary": "#FFFFFF",
        "on-primary-fixed-variant": "#930007",
        "on-background": "#ffdad5",
        "tertiary-fixed": "#d5e3ff",
        "on-tertiary": "#003061",
        "surface": "#200e0c"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "stack-lg": "32px",
        "gutter": "24px",
        "margin-mobile": "16px",
        "container-max": "1440px",
        "stack-sm": "8px",
        "stack-md": "16px",
        "margin-desktop": "48px"
      },
      fontFamily: {
        "headline-lg": ["var(--font-outfit)", "sans-serif"],
        "label-caps": ["var(--font-inter)", "sans-serif"],
        "body-lg": ["var(--font-inter)", "sans-serif"],
        "headline-md": ["var(--font-outfit)", "sans-serif"],
        "body-md": ["var(--font-inter)", "sans-serif"],
        "display-hero": ["var(--font-outfit)", "sans-serif"],
        "display-hero-mobile": ["var(--font-outfit)", "sans-serif"],
        // Adding default fallbacks in case standard classes are used
        "sans": ["var(--font-inter)", "sans-serif"],
        "display": ["var(--font-outfit)", "sans-serif"],
      },
      fontSize: {
        "headline-lg": ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "700" }],
        "label-caps": ["12px", { lineHeight: "1", letterSpacing: "0.15em", fontWeight: "700" }],
        "body-lg": ["18px", { lineHeight: "1.6", fontWeight: "400" }],
        "headline-md": ["24px", { lineHeight: "1.3", fontWeight: "700" }],
        "body-md": ["16px", { lineHeight: "1.5", fontWeight: "400" }],
        "display-hero": ["72px", { lineHeight: "1.1", letterSpacing: "-0.04em", fontWeight: "900" }],
        "display-hero-mobile": ["40px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "900" }]
      }
    }
  },
  plugins: [],
};
export default config;
