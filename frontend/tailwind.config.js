/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        bnk: {
          navy: '#123C69',
          blue: '#1E6FD9',
          gold: '#F2B705',
          gray: '#F5F7FA'
        }
      }
    }
  },
  plugins: []
}
