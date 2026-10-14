// lib/history.ts - Plan history connected to FastAPI backend with local cache fallback
import { API_BASE_URL, getStoredToken } from "./api"

const HISTORY_PREFIX = "terra_history_"

export interface Plan {
  id: string
  fieldId?: string
  fieldName?: string
  season: string
  strategy: string
  crops: { name: string; acres: number }[]
  profit: string
  waterSaved: string
  fertilizerSaved: string
  status: "Current" | "Completed"
  createdAt: string
}

function getStorageKey(userId: string): string {
  return `${HISTORY_PREFIX}${userId}`
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

/** De-duplicate plans by id, keeping first occurrence (most recent) */
function deduplicatePlans(plans: Plan[]): Plan[] {
  const seen = new Set<string>()
  return plans.filter((p) => {
    if (seen.has(p.id)) return false
    seen.add(p.id)
    return true
  })
}

export async function getHistory(userId: string, fieldId?: string): Promise<Plan[]> {
  const token = getStoredToken()
  const url = `${API_BASE_URL}/history/plans${fieldId ? `?field_id=${encodeURIComponent(fieldId)}` : ""}`
  try {
    const res = await fetch(url, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
    if (res.ok) {
      const plans: Plan[] = await res.json()
      if (Array.isArray(plans)) {
        const deduped = deduplicatePlans(plans)
        if (!fieldId) {
          // Sync local cache with backend truth when querying all
          safeSetItem(getStorageKey(userId), JSON.stringify(deduped))
        }
        return deduped
      }
    }
  } catch {}

  // Local storage fallback — still deduplicate in case of stale data
  const cached = safeGetItem(getStorageKey(userId))
  if (cached) {
    try {
      const parsed: Plan[] = JSON.parse(cached)
      const filtered = fieldId ? parsed.filter((p) => p.fieldId === fieldId) : parsed
      return deduplicatePlans(filtered)
    } catch {}
  }

  // No data at all — return empty
  return []
}

export async function addPlan(
  userId: string,
  plan: Omit<Plan, "id" | "createdAt">
): Promise<Plan> {
  const token = getStoredToken()
  try {
    const res = await fetch(`${API_BASE_URL}/history/plans`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(plan),
    })

    if (res.ok) {
      const savedPlan: Plan = await res.json()
      // Invalidate local cache — next getHistory() will fetch fresh from backend
      safeRemoveItem(getStorageKey(userId))
      return savedPlan
    }
    const errText = await res.text().catch(() => "")
    throw new Error(`Server error ${res.status}: ${errText}`)
  } catch (err) {
    // If backend save failed, still provide a local-only fallback (offline mode)
    const newPlan: Plan = {
      ...plan,
      id: `plan-local-${Date.now()}`,
      createdAt: new Date().toISOString(),
    }

    // Update cache carefully without duplicating
    const cached = safeGetItem(getStorageKey(userId))
    let existing: Plan[] = []
    if (cached) {
      try { existing = JSON.parse(cached) } catch {}
    }
    const updated = deduplicatePlans([newPlan, ...existing])
    safeSetItem(getStorageKey(userId), JSON.stringify(updated))
    return newPlan
  }
}

export async function deletePlan(userId: string, planId: string): Promise<void> {
  const token = getStoredToken()
  try {
    await fetch(`${API_BASE_URL}/history/plans/${planId}`, {
      method: "DELETE",
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    })
  } catch {}
  // Invalidate cache
  safeRemoveItem(getStorageKey(userId))
}