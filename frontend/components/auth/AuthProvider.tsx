"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from "react"
import { getCurrentUser, isLoggedIn, logout as authLogout, type User } from "@/lib/auth"

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<{ user: User } | { error: string }>
  register: (data: { name: string; email: string; password: string; village?: string }) => Promise<{ user: User } | { error: string }>
  logout: () => void
  updateProfile: (patch: Partial<Pick<User, "name" | "village" | "district" | "farmSizeAcres" | "soilType" | "language">>) => Promise<{ user: User } | { error: string }>
  refreshUser: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    const currentUser = getCurrentUser()
    const { getStoredToken, setStoredToken, API_BASE_URL } = await import("@/lib/api")
    const token = getStoredToken()

    // If user is cached without token, attempt auto-login for demo farmer or verify token
    if (currentUser && !token && currentUser.email === "ramesh.patil@gmail.com") {
      try {
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: "ramesh.patil@gmail.com", password: "terra123" }),
        })
        if (res.ok) {
          const data = await res.json()
          setStoredToken(data.access_token)
          setUser(data.user)
          return
        }
      } catch {}
    }
    setUser(currentUser)
  }

  useEffect(() => {
    // Initial load
    refreshUser().finally(() => setLoading(false))

    // Listen for storage changes (e.g., logout in another tab)
    const handleStorageChange = () => {
      refreshUser()
    }
    window.addEventListener("storage", handleStorageChange)
    return () => window.removeEventListener("storage", handleStorageChange)
  }, [])

  const login = async (email: string, password: string) => {
    const result = await (await import("@/lib/auth")).login(email, password)
    if ("user" in result) {
      setUser(result.user)
    }
    return result
  }

  const register = async (data: { name: string; email: string; password: string; village?: string }) => {
    const result = await (await import("@/lib/auth")).register(data)
    if ("user" in result) {
      setUser(result.user)
    }
    return result
  }

  const logout = () => {
    authLogout()
    setUser(null)
  }

  const updateProfile = async (patch: Partial<Pick<User, "name" | "village" | "district" | "farmSizeAcres" | "soilType" | "language">>) => {
    const result = await (await import("@/lib/auth")).updateProfile(patch)
    if ("user" in result) {
      setUser(result.user)
    }
    return result
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateProfile, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}