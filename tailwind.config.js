/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./assets/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        kerinci: {
          light: '#e8f5e9',
          DEFAULT: '#1b5e20',
          dark: '#144d17',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
