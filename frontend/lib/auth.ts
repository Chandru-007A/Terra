// lib/auth.ts - Authenticated farmer session management connected to FastAPI backend
import { API_BASE_URL, setStoredToken, removeStoredToken, getStoredToken } from "./api"

const USERS_KEY = "terra_users"
const SESSION_KEY = "terra_session"
const CURRENT_USER_KEY = "terra_current_user"

export interface User {
  id: string
  name: string
  email: string
  passwordHash?: string
  village?: string
  district?: string
  farmSizeAcres?: number
  soilType?: string
  language?: string
  createdAt: string
}

function safeGetItem(key: string): string | null {
  if (typeof window === "undefined") return null
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeSetItem(key: string, value: string): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(key, value)
  } catch {}
}

function safeRemoveItem(key: string): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(key)
  } catch {}
}

// Seed default demo profile for offline fallback
function getDefaultDemoUser(): User {
  return {
    id: "demo-user-1",
    name: "Ramesh Patil",
    email: "ramesh.patil@gmail.com",
    village: "Nashik",
    district: "Maharashtra",
    farmSizeAcres: 10,
    soilType: "Black cotton soil",
    language: "English",
    createdAt: new Date().toISOString(),
  }
}

export async function register(data: {
  name: string
  email: string
  password: string
  village?: string
}): Promise<{ user: User } | { error: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.name,
        email: data.email,
        password: data.password,
        village: data.village,
      }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return { error: err.detail || "Registration failed" }
    }

    const json = await res.json()
    const user: User = json.user
    setStoredToken(json.access_token)
    safeSetItem(SESSION_KEY, user.id)
    safeSetItem(CURRENT_USER_KEY, JSON.stringify(user))
    return { user }
  } catch (e: any) {
    // Offline / fallback registration
    const fallbackUser: User = {
      id: `user-${Date.now()}`,
      name: data.name.trim(),
      email: data.email.toLowerCase(),
      village: data.village?.trim(),
      createdAt: new Date().toISOString(),
    }
    safeSetItem(SESSION_KEY, fallbackUser.id)
    safeSetItem(CURRENT_USER_KEY, JSON.stringify(fallbackUser))
    return { user: fallbackUser }
  }
}

export async function login(
  email: string,
  password: string
): Promise<{ user: User } | { error: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return { error: err.detail || "Email or password is wrong" }
    }

    const json = await res.json()
    const user: User = json.user
    setStoredToken(json.access_token)
    safeSetItem(SESSION_KEY, user.id)
    safeSetItem(CURRENT_USER_KEY, JSON.stringify(user))
    return { user }
  } catch (e) {
    // Demo fallback for local development without active network
    if (email.toLowerCase() === "ramesh.patil@gmail.com") {
      const demoUser = getDefaultDemoUser()
      safeSetItem(SESSION_KEY, demoUser.id)
      safeSetItem(CURRENT_USER_KEY, JSON.stringify(demoUser))
      return { user: demoUser }
    }
    return { error: "Failed to connect to authentication server" }
  }
}

export function logout(): void {
  removeStoredToken()
  safeRemoveItem(SESSION_KEY)
  safeRemoveItem(CURRENT_USER_KEY)
}

export function getCurrentUser(): User | null {
  const cached = safeGetItem(CURRENT_USER_KEY)
  if (cached) {
    try {
      return JSON.parse(cached)
    } catch {}
  }
  // No cached user and no token: not logged in
  return null
}

export async function updateProfile(
  patch: Partial<Pick<User, "name" | "village" | "district" | "farmSizeAcres" | "soilType" | "language">>
): Promise<{ user: User } | { error: string }> {
  const token = getStoredToken()
  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(patch),
    })

    if (res.ok) {
      const updatedUser: User = await res.json()
      safeSetItem(CURRENT_USER_KEY, JSON.stringify(updatedUser))
      return { user: updatedUser }
    }
  } catch {}

  // Fallback update in local storage
  const current = getCurrentUser() || getDefaultDemoUser()
  const updatedUser = { ...current, ...patch }
  safeSetItem(CURRENT_USER_KEY, JSON.stringify(updatedUser))
  return { user: updatedUser }
}

export function isLoggedIn(): boolean {
  // Only consider logged in if there is an actual stored token
  return !!getStoredToken()
}

export function getSessionUserId(): string | null {
  return safeGetItem(SESSION_KEY)
}