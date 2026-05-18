/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        primary: '#6366f1',
        secondary: '#8b5cf6',
        accent: '#06b6d4',
        textMain: '#f8fafc',
        textMuted: '#94a3b8'
      }
    },
  },
  plugins: [],
}
