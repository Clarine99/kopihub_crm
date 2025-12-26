/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ["Space Grotesk", "Work Sans", "sans-serif"],
        body: ["Work Sans", "Space Grotesk", "sans-serif"]
      },
      colors: {
        ink: "#0b0d12",
        smoke: "#111827",
        glow: "#1b2030",
        accent: "#f4b942",
        accent2: "#4fd1c5"
      },
      boxShadow: {
        panel: "0 30px 80px rgba(0, 0, 0, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;
