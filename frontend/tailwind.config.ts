import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  // The KERN design system is expressed as CSS custom properties in
  // app/globals.css (single source of truth for colour, type and elevation).
  // Tailwind is kept here only for layout/spacing utilities — it deliberately
  // does NOT redefine brand colours, fonts or shadows, so there is no second
  // palette to drift out of sync.
  theme: {
    extend: {
      borderRadius: {
        'xl':  '14px',
        '2xl': '20px',
        '3xl': '24px',
      },
    },
  },
  plugins: [],
}

export default config
