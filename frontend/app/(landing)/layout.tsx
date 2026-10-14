import type React from "react"
import "./landing.css"

export default function LandingLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return <div className="bg-[#0B0C0F] min-h-screen text-foreground">{children}</div>
}
