// lib/api.ts - Central API client for TERRA FastAPI backend

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const TOKEN_KEY = "terra_access_token"

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {}
}

export function removeStoredToken(): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {}
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`
  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorMsg = `API request failed with status ${response.status}`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {}
    throw new Error(errorMsg)
  }

  return response.json() as Promise<T>
}

// ----------------------------------------------------
// API Service Methods
// ----------------------------------------------------

export interface ApiCropItem {
  id: number
  crop_id: string
  emoji: string
  title: string
  suitability: string
  status: "in" | "out"
  yield: string
  sow: string
  profit: string
  water: string
  variant: "default" | "secondary" | "outline"
  expected_yield_q: number
  expected_profit: number
  water_requirement_kl: number
  fertilizer_kg: number
  cost_per_acre: number
  market_price_per_q: number
  key_advantages: string[]
  irrigation_advice: string
}

export interface CropRecommendationParams {
  n?: number
  p?: number
  k?: number
  ph?: number
  temperature?: number
  humidity?: number
  rainfall?: number
  season?: string
  top_k?: number
}

export async function apiRecommendCrops(
  params: CropRecommendationParams = {}
): Promise<{ count: number; crops: ApiCropItem[] }> {
  return apiFetch<{ count: number; crops: ApiCropItem[] }>("/recommend/crops", {
    method: "POST",
    body: JSON.stringify({
      n: params.n ?? 80,
      p: params.p ?? 45,
      k: params.k ?? 70,
      ph: params.ph ?? 7.2,
      temperature: params.temperature ?? 22,
      humidity: params.humidity ?? 60,
      rainfall: params.rainfall ?? 420,
      season: params.season ?? "Rabi",
      top_k: params.top_k ?? 10,
    }),
  })
}

export interface ApiAllocationResult {
  strategy: string
  status: string
  total_land_allocated_acres: number
  total_land_available_acres: number
  total_water_used_kl: number
  total_water_available_kl: number
  water_saved_percent: number
  water_saved_str: string
  total_fertilizer_used_kg: number
  total_fertilizer_available_kg: number
  fertilizer_saved_percent: number
  fertilizer_saved_str: string
  total_budget_used_inr: number
  total_budget_available_inr: number
  budget_used_str: string
  expected_total_production_q: number
  expected_production_str: string
  expected_net_profit_inr: number
  expected_profit_str: string
  profit_increase_percent: number
  crops: {
    crop_id: string
    name: string
    emoji: string
    acres: number
    expected_yield_q: number
    expected_profit_inr: number
    formatted_profit: string
    water_used_kl: number
    cost_inr: number
    profit_margin_percent: number
    status: string
  }[]
  constraints_summary: {
    land_utilization_percent: number
    water_utilization_percent: number
    fertilizer_utilization_percent: number
    budget_utilization_percent: number
  }
}

export async function apiOptimizeAllocation(params: {
  crop_ids?: string[]
  total_land_acres?: number
  water_available_kl?: number
  fertilizer_available_kg?: number
  total_budget_inr?: number
  strategy?: string
} = {}): Promise<ApiAllocationResult> {
  return apiFetch<ApiAllocationResult>("/optimize/allocate", {
    method: "POST",
    body: JSON.stringify({
      crop_ids: params.crop_ids ?? ["onion", "wheat", "chickpea", "mustard"],
      total_land_acres: params.total_land_acres ?? 10,
      water_available_kl: params.water_available_kl ?? 16000,
      fertilizer_available_kg: params.fertilizer_available_kg ?? 1000,
      total_budget_inr: params.total_budget_inr ?? 400000,
      strategy: params.strategy ?? "balanced",
    }),
  })
}

export async function apiCompareStrategies(params: {
  crop_ids?: string[]
  total_land_acres?: number
  water_available_kl?: number
  fertilizer_available_kg?: number
  total_budget_inr?: number
} = {}): Promise<{ strategies: ApiAllocationResult[] }> {
  return apiFetch<{ strategies: ApiAllocationResult[] }>("/optimize/strategies", {
    method: "POST",
    body: JSON.stringify({
      crop_ids: params.crop_ids ?? ["onion", "wheat", "chickpea", "mustard"],
      total_land_acres: params.total_land_acres ?? 10,
      water_available_kl: params.water_available_kl ?? 16000,
      fertilizer_available_kg: params.fertilizer_available_kg ?? 1000,
      total_budget_inr: params.total_budget_inr ?? 400000,
    }),
  })
}

export async function apiPredictYield(params: {
  crop_id: string
  n?: number
  p?: number
  k?: number
  ph?: number
  temperature?: number
  rainfall?: number
  water_available_kl?: number
  fertilizer_applied_kg?: number
}) {
  return apiFetch("/predict/yield", {
    method: "POST",
    body: JSON.stringify(params),
  })
}
