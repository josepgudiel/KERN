import type { Metadata } from 'next'
import { IBM_Plex_Sans, JetBrains_Mono, Outfit } from 'next/font/google'
import './globals.css'
import { SessionProvider } from '@/context/SessionContext'

/* Type system — three families, shared by the marketing page and the
   application so the two read as one product. IBM Plex Sans is humanist and
   carries body copy without competing. JetBrains Mono is the *figure* voice
   and nothing else: it ships true tabular figures, which is what makes a
   column of revenue line up. Setting labels and navigation in it, as this app
   previously did, is what made a business tool look like a terminal. */
const plexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  variable: '--font-body',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-mono',
  display: 'swap',
})

/* Headline and label voice everywhere. Outfit is a geometric sans with
   near-circular bowls and a flat, even rhythm — it holds a confident line at
   display scale on the marketing page and stays sober at 0.74rem on a stat
   tile, which is what lets one family cover both. */
const outfit = Outfit({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-heading',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Kern by Analytic',
  description: 'Turn your sales data into ranked, actionable recommendations.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plexSans.variable} ${jetbrainsMono.variable} ${outfit.variable}`}>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
