/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./assets/templates/**/*.html",
    "./**/views.py",
  ],
  theme: {
    extend: {
      colors: {
        'brand-blue': '#2563EB',
        'brand-bg': '#F8F9FA'
      }
    },
  },
  plugins: [],
}
