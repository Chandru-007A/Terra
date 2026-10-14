// lib/fields.ts - Field-centric API client for farm plots, soil, resources, and crops
import { apiFetch, ApiCropItem } from "./api"

export interface FieldCropItem {
  cropId: string
  name: string
  acres: number
  sow?: string
  season?: string
  status?: string
}

export interface Field {
  id: string
  userId: string
  name: string
  areaAcres: number
  soilType: string
  location: string
  n: number
  p: number
  k: number
  ph: number
  waterAvailableKl: number
  fertilizerAvailableKg: number
  budgetInr: number
  crops: FieldCropItem[]
  activePlanId?: string
  activeStrategy?: string
  createdAt: string
}

export interface FieldCreateInput {
  name: string
  areaAcres: number
  soilType: string
  location: string
  waterAvailableKl?: number
  fertilizerAvailableKg?: number
  budgetInr?: number
  crops?: FieldCropItem[]
}

export interface FieldUpdateInput {
  name?: string
  areaAcres?: number
  soilType?: string
  location?: string
  n?: number
  p?: number
  k?: number
  ph?: number
  waterAvailableKl?: number
  fertilizerAvailableKg?: number
  budgetInr?: number
  crops?: FieldCropItem[]
  activePlanId?: string
  activeStrategy?: string
}

export async function apiGetFields(): Promise<Field[]> {
  return apiFetch<Field[]>("/fields", { method: "GET" })
}

export async function apiGetField(fieldId: string): Promise<Field> {
  return apiFetch<Field>(`/fields/${fieldId}`, { method: "GET" })
}

export async function apiCreateField(input: FieldCreateInput): Promise<Field> {
  return apiFetch<Field>("/fields", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function apiUpdateField(
  fieldId: string,
  input: FieldUpdateInput
): Promise<Field> {
  return apiFetch<Field>(`/fields/${fieldId}`, {
    method: "PUT",
    body: JSON.stringify(input),
  })
}

export async function apiDeleteField(fieldId: string): Promise<void> {
  return apiFetch<void>(`/fields/${fieldId}`, {
    method: "DELETE",
  })
}

export async function apiAddFieldCrop(
  fieldId: string,
  crop: FieldCropItem
): Promise<Field> {
  return apiFetch<Field>(`/fields/${fieldId}/crops`, {
    method: "POST",
    body: JSON.stringify(crop),
  })
}

export async function apiRemoveFieldCrop(
  fieldId: string,
  cropId: string
): Promise<Field> {
  return apiFetch<Field>(`/fields/${fieldId}/crops/${encodeURIComponent(cropId)}`, {
    method: "DELETE",
  })
}

export async function apiGetFieldRecommendations(
  fieldId: string,
  season: string = "Rabi",
  topK: number = 20
): Promise<{ count: number; crops: ApiCropItem[] }> {
  return apiFetch<{ count: number; crops: ApiCropItem[] }>(
    `/fields/${fieldId}/recommendations?season=${encodeURIComponent(season)}&top_k=${topK}`,
    { method: "GET" }
  )
}
