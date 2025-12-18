import type { Metadata } from "next";
import { Inter } from 'next/font/google';
import "./globals.css";
import { ThemeProvider } from '@/components/ThemeProvider';
import { ActivityTrackerProvider } from '@/components/ActivityTrackerProvider';
import { UIProvider } from '@/contexts/UIContext';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NeuroVest - AI-Powered Stock Market Analysis",
  description: "Advanced AI algorithms for real-time stock predictions, sentiment analysis, and market insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider>
          <ActivityTrackerProvider>
            <UIProvider>
              {children}
            </UIProvider>
          </ActivityTrackerProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
