import type { Metadata } from "next";
import { Be_Vietnam_Pro, Space_Grotesk } from "next/font/google";
import { AppShell } from "./components/shell/app-shell";
import "./globals.css";

// Saigon Digital: Space Grotesk for display, Be Vietnam Pro for body (full Vietnamese support).
const display = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
});

const body = Be_Vietnam_Pro({
  variable: "--font-be-vietnam",
  subsets: ["latin", "vietnamese"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "SEO Report Generator",
  description: "Bi-weekly SEO report for the CS team",
  icons: { icon: "/brand/logo-symbol-blue.svg" },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} antialiased`}>
      <body className="flex min-h-[100dvh] flex-col">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
