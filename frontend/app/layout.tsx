import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Study Planner",
  description: "Chat with your own notes. A RAG-powered study planner and exam stress companion.",
  authors: [{ name: "Study Planner" }],
  openGraph: {
    title: "Study Planner",
    description: "Chat with your own notes. A RAG-powered study planner and exam stress companion.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
