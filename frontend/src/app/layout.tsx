import type { Metadata } from "next";
import { Newsreader, Geist, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import "../../../design-system/colors_and_type.css";
import "../../../design-system/ui_kits/web_app/app.css";

const newsreader = Newsreader({
  variable: "--font-display",
  subsets: ["latin"],
  style: ["normal", "italic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const geist = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Prism — daily brief",
  description: "Intelligence, refracted for who you are.",
  icons: { icon: "/prism-mark.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${newsreader.variable} ${geist.variable} ${jetbrainsMono.variable}`}
    >
      <body className="time-sand">{children}</body>
    </html>
  );
}
