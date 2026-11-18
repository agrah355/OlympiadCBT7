import './globals.css';
export const metadata = { title: 'OlympiadCBT', description: 'Focused science olympiad computer-based testing' };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
