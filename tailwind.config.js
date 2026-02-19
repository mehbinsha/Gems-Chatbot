const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: ['./frontend/**/*.{html,js}'],
  theme: {
    extend: {
      colors: {
        'gem-green': '#10b981',
      },
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
    },
  },
  plugins: [],
};
