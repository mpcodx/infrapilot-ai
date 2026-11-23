/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        infrapilot: {
          950: "#070a12",
          900: "#0c1322",
          850: "#111b30",
          800: "#182440",
          700: "#24365d",
          accent: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
        piops: {
          950: "#070a12",
          900: "#0c1322",
          850: "#111b30",
          800: "#182440",
          700: "#24365d",
          accent: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      },
    },
  },
  plugins: [],
};
