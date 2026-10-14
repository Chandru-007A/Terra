"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/components/auth/AuthProvider"
import { useRouter, usePathname } from "next/navigation"
import { Loader2 } from "lucide-react"

import { FieldProvider } from "@/lib/field-context"

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !authLoading && !user) {
      // Not logged in - redirect to login with next parameter
      router.push(`/login?next=${encodeURIComponent(pathname)}`)
    }
  }, [mounted, authLoading, user, router, pathname])

  // Show neutral spinner while checking auth
  if (!mounted || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render children if not authenticated (will redirect)
  if (!user) {
    return null
  }

  return (
    <FieldProvider>
      {children}
    </FieldProvider>
  )
}