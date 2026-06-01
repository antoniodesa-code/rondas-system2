/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        hospital: {
          blue: '#1e40af',
          green: '#15803d',
          red: '#b91c1c',
          yellow: '#a16207',
        },
      },
    },
  },
  plugins: [],
}
