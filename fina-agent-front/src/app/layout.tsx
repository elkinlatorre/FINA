import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FINA - Agentic Finance Dashboard",
  description: "Advanced AI-powered financial orchestration and portfolio analysis.",
};

import { AuthProvider } from "@/hooks/useAuth";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
