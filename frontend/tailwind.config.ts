import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d0d11',
        accent: '#6fffe9',
        text: '#eaeaea'
      }
    }
  },
  plugins: []
};

export default config;
