import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/components/theme-provider"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "TERRA — Smart Farm Planner",
  description: "AI crop recommendation and resource optimization for farmers",
  generator: "v0.app",
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className="font-sans antialiased"><ThemeProvider defaultTheme="light" storageKey="terra-theme">{children}</ThemeProvider><Analytics /></body></html>
}
