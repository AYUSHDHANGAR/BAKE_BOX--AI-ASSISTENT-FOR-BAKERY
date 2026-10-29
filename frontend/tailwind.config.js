/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bakery: {
          50: '#fffbf5',
          100: '#fbf0e4',
          200: '#f7dec9',
          300: '#f1c4a4',
          400: '#e9a177',
          500: '#e18051',
          600: '#d26438',
          700: '#af4b2c',
          800: '#8c3c27',
          900: '#723423',
        },
        choco: {
          800: '#2c1810',
          900: '#1a0e0a',
        }
      }
    },
  },
  plugins: [],
}
