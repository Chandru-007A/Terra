"use client"

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react"
import {
  Field,
  FieldCreateInput,
  FieldUpdateInput,
  FieldCropItem,
  apiGetFields,
  apiCreateField,
  apiUpdateField,
  apiDeleteField,
  apiAddFieldCrop,
  apiRemoveFieldCrop,
} from "./fields"
import { useAuth } from "@/components/auth/AuthProvider"
import { toast } from "sonner"

const STORAGE_SELECTED_KEY = "terra_selected_field_id"

interface FieldContextType {
  fields: Field[]
  selectedField: Field | null
  selectedFieldId: string | "all"
  loading: boolean
  setSelectedFieldId: (id: string | "all") => void
  refreshFields: () => Promise<void>
  createField: (data: FieldCreateInput) => Promise<Field>
  updateField: (id: string, data: FieldUpdateInput) => Promise<Field>
  deleteField: (id: string) => Promise<void>
  addCrop: (fieldId: string, crop: FieldCropItem) => Promise<Field>
  removeCrop: (fieldId: string, cropId: string) => Promise<Field>
}

const FieldContext = createContext<FieldContextType | undefined>(undefined)

export function FieldProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [fields, setFields] = useState<Field[]>([])
  const [selectedFieldId, setSelectedFieldIdState] = useState<string | "all">("all")
  const [loading, setLoading] = useState(true)

  const selectedField =
    selectedFieldId === "all"
      ? null
      : fields.find((f) => f.id === selectedFieldId) || null

  const setSelectedFieldId = (id: string | "all") => {
    setSelectedFieldIdState(id)
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_SELECTED_KEY, id)
      } catch {}
    }
  }

  const refreshFields = useCallback(async () => {
    if (!user) {
      setFields([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const data = await apiGetFields()
      setFields(data)

      // Restore saved selection or default to first field if available
      let savedId: string | null = null
      if (typeof window !== "undefined") {
        try {
          savedId = localStorage.getItem(STORAGE_SELECTED_KEY)
        } catch {}
      }

      if (savedId === "all") {
        setSelectedFieldIdState("all")
      } else if (savedId && data.some((f) => f.id === savedId)) {
        setSelectedFieldIdState(savedId)
      } else if (data.length > 0) {
        setSelectedFieldIdState(data[0].id)
      } else {
        setSelectedFieldIdState("all")
      }
    } catch {
      // Offline fallback: keep existing fields
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    refreshFields()
  }, [refreshFields])

  const createField = async (data: FieldCreateInput): Promise<Field> => {
    try {
      const newField = await apiCreateField(data)
      setFields((prev) => [...prev, newField])
      // Automatically select newly created field
      setSelectedFieldId(newField.id)
      return newField
    } catch (err: any) {
      toast.error(err.message || "Failed to create field")
      throw err
    }
  }

  const updateField = async (id: string, data: FieldUpdateInput): Promise<Field> => {
    try {
      const updated = await apiUpdateField(id, data)
      setFields((prev) => prev.map((f) => (f.id === id ? updated : f)))
      return updated
    } catch (err: any) {
      toast.error(err.message || "Failed to update field")
      throw err
    }
  }

  const deleteField = async (id: string): Promise<void> => {
    try {
      await apiDeleteField(id)
      setFields((prev) => {
        const remaining = prev.filter((f) => f.id !== id)
        if (selectedFieldId === id) {
          const nextId = remaining.length > 0 ? remaining[0].id : "all"
          setSelectedFieldId(nextId)
        }
        return remaining
      })
    } catch (err: any) {
      toast.error(err.message || "Failed to delete field")
      throw err
    }
  }

  const addCrop = async (fieldId: string, crop: FieldCropItem): Promise<Field> => {
    try {
      const updated = await apiAddFieldCrop(fieldId, crop)
      setFields((prev) => prev.map((f) => (f.id === fieldId ? updated : f)))
      return updated
    } catch (err: any) {
      toast.error(err.message || "Failed to add crop to field")
      throw err
    }
  }

  const removeCrop = async (fieldId: string, cropId: string): Promise<Field> => {
    try {
      const updated = await apiRemoveFieldCrop(fieldId, cropId)
      setFields((prev) => prev.map((f) => (f.id === fieldId ? updated : f)))
      return updated
    } catch (err: any) {
      toast.error(err.message || "Failed to remove crop from field")
      throw err
    }
  }

  return (
    <FieldContext.Provider
      value={{
        fields,
        selectedField,
        selectedFieldId,
        loading,
        setSelectedFieldId,
        refreshFields,
        createField,
        updateField,
        deleteField,
        addCrop,
        removeCrop,
      }}
    >
      {children}
    </FieldContext.Provider>
  )
}

export function useField() {
  const context = useContext(FieldContext)
  if (!context) {
    throw new Error("useField must be used within a FieldProvider")
  }
  return context
}
