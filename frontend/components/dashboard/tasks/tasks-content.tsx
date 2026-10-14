"use client"

import { useState, useEffect, useMemo } from "react"
import { Calendar, Filter, Search, Tag, Loader2, Sprout, Info, Check, Plus } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { apiRecommendCrops, type ApiCropItem } from "@/lib/api"
import { apiGetFieldRecommendations } from "@/lib/fields"
import { useField } from "@/lib/field-context"
import { toast } from "sonner"

const initialCatalogueCrops = [
  { id: 1, crop_id: "onion", emoji: "🧅", title: "Onion (Rabi)", suitability: "92% Highly Suitable", status: "out", yield: "90 q/acre", sow: "Oct 25 – Nov 15", profit: "₹74,000/acre", water: "High", variant: "default" as const },
  { id: 2, crop_id: "chickpea", emoji: "🫘", title: "Chickpea (Gram)", suitability: "88% Highly Suitable", status: "out", yield: "8 q/acre", sow: "Oct 15 – Nov 10", profit: "₹30,400/acre", water: "Low", variant: "default" as const },
  { id: 3, crop_id: "wheat", emoji: "🌾", title: "Wheat (Rabi)", suitability: "81% Suitable", status: "out", yield: "18 q/acre", sow: "Nov 1 – Nov 25", profit: "₹23,000/acre", water: "Medium", variant: "secondary" as const },
  { id: 4, crop_id: "mustard", emoji: "🌼", title: "Mustard (Rabi)", suitability: "67% Moderate", status: "out", yield: "7 q/acre", sow: "Oct 10 – Oct 31", profit: "₹21,500/acre", water: "Low", variant: "outline" as const },
  { id: 5, crop_id: "sorghum", emoji: "🌿", title: "Sorghum (Rabi Jowar)", suitability: "63% Moderate", status: "out", yield: "9 q/acre", sow: "Oct 1 – Oct 20", profit: "₹12,000/acre", water: "Low", variant: "outline" as const },
  { id: 6, crop_id: "safflower", emoji: "🟡", title: "Safflower", suitability: "58% Moderate", status: "out", yield: "6 q/acre", sow: "Oct 5 – Nov 5", profit: "₹14,500/acre", water: "Low", variant: "outline" as const },
  { id: 7, crop_id: "potato", emoji: "🥔", title: "Potato (Rabi)", suitability: "75% Suitable", status: "out", yield: "100 q/acre", sow: "Oct 15 – Nov 15", profit: "₹65,000/acre", water: "High", variant: "secondary" as const },
  { id: 8, crop_id: "garlic", emoji: "🧄", title: "Garlic (Rabi)", suitability: "72% Suitable", status: "out", yield: "30 q/acre", sow: "Oct 20 – Nov 15", profit: "₹80,000/acre", water: "Medium", variant: "secondary" as const },
  { id: 9, crop_id: "lentil", emoji: "🫘", title: "Lentil (Masoor)", suitability: "68% Moderate", status: "out", yield: "7 q/acre", sow: "Oct 20 – Nov 15", profit: "₹24,000/acre", water: "Low", variant: "outline" as const },
  { id: 10, crop_id: "tomato", emoji: "🍅", title: "Tomato", suitability: "78% Suitable", status: "out", yield: "120 q/acre", sow: "Year-round", profit: "₹95,000/acre", water: "High", variant: "secondary" as const },
]

export function TasksContent({ onOpenAddCrop }: { onOpenAddCrop?: () => void } = {}) {
  const { selectedField, addCrop, removeCrop } = useField()
  const [filter, setFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [season, setSeason] = useState("Rabi")
  const [catalogCrops, setCatalogCrops] = useState<any[]>(initialCatalogueCrops)
  const [loading, setLoading] = useState(false)
  const [togglingCropId, setTogglingCropId] = useState<string | null>(null)

  const seasonsList = ["Rabi", "Kharif", "Zaid", "All"]

  // Load crop catalogue from API tailored to field and season
  useEffect(() => {
    let isMounted = true
    async function loadCrops() {
      try {
        setLoading(true)
        let res: { count: number; crops: ApiCropItem[] }

        if (selectedField) {
          res = await apiGetFieldRecommendations(selectedField.id, season, 20)
        } else {
          res = await apiRecommendCrops({ season: season, top_k: 20 })
        }

        if (isMounted && res.crops && res.crops.length > 0) {
          setCatalogCrops(res.crops)
        }
      } catch {
        // Keeps fallback catalogue if offline
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadCrops()
    return () => {
      isMounted = false
    }
  }, [season, selectedField?.id])

  // Derive field-calibrated crop list:
  // The selected field is the SINGLE SOURCE OF TRUTH for what is "In Plan" vs "Not in Plan"
  const crops = useMemo(() => {
    const assignedMap = new Map<string, any>()
    if (selectedField?.crops) {
      for (const fc of selectedField.crops) {
        if (fc.status !== "out") {
          assignedMap.set(fc.cropId.toLowerCase(), fc)
          assignedMap.set(fc.name.toLowerCase(), fc)
        }
      }
    }

    // Map catalogue recommendations with field-assigned status
    const list = catalogCrops.map((c, i) => {
      const cropKey = (c.crop_id || "").toLowerCase()
      const titleKey = (c.title || "").toLowerCase()
      const isAssigned = assignedMap.has(cropKey) || assignedMap.has(titleKey)
      const assignedItem = assignedMap.get(cropKey) || assignedMap.get(titleKey)

      return {
        id: c.id || i + 1,
        crop_id: c.crop_id || `crop-${i + 1}`,
        emoji: c.emoji || "🌱",
        title: c.title,
        suitability: c.suitability,
        status: isAssigned ? ("in" as const) : ("out" as const),
        yield: c.yield,
        sow: c.sow,
        profit: c.profit,
        water: c.water,
        variant: c.variant || "default",
        acres: assignedItem?.acres,
      }
    })

    // If field has saved crops that aren't in the catalogue, prepend them
    if (selectedField?.crops) {
      for (const fc of selectedField.crops) {
        if (fc.status !== "out") {
          const fcKey = fc.cropId.toLowerCase()
          const exists = list.some(
            (item) => item.crop_id.toLowerCase() === fcKey || item.title.toLowerCase() === fc.name.toLowerCase()
          )
          if (!exists) {
            list.unshift({
              id: 5000 + list.length,
              crop_id: fc.cropId,
              emoji: "🌱",
              title: fc.name,
              suitability: "Assigned Plan",
              status: "in" as const,
              yield: "Field Allocation",
              sow: fc.sow || "Seasonal window",
              profit: `${fc.acres} Acres`,
              water: "Field Scoped",
              variant: "default" as const,
              acres: fc.acres,
            })
          }
        }
      }
    }

    return list
  }, [catalogCrops, selectedField?.crops])

  const toggleCropStatus = async (id: number | string) => {
    const targetCrop = crops.find((c) => c.id === id)
    if (!targetCrop || !selectedField) return

    setTogglingCropId(targetCrop.crop_id)
    const willBeIn = targetCrop.status !== "in"

    try {
      if (willBeIn) {
        const defaultAcres = Math.max(1.0, Math.round((selectedField.areaAcres / 3) * 10) / 10)
        await addCrop(selectedField.id, {
          cropId: targetCrop.crop_id,
          name: targetCrop.title,
          acres: targetCrop.acres || defaultAcres,
          sow: targetCrop.sow,
          season: `${season} 2026-27`,
          status: "in",
        })
        toast.success(`${targetCrop.title} added to ${selectedField.name} plan`)
      } else {
        await removeCrop(selectedField.id, targetCrop.crop_id)
        toast.success(`${targetCrop.title} removed from ${selectedField.name} plan`)
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update crop plan")
    } finally {
      setTogglingCropId(null)
    }
  }

  const cycleSeason = () => {
    const nextIdx = (seasonsList.indexOf(season) + 1) % seasonsList.length
    setSeason(seasonsList[nextIdx])
  }

  const searchFiltered = searchQuery.trim()
    ? crops.filter(
        (c) =>
          c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.suitability.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : crops

  const countTotal = searchFiltered.length
  const countIn = searchFiltered.filter((c) => c.status === "in").length
  const countOut = searchFiltered.filter((c) => c.status === "out").length

  const filteredCrops =
    filter === "all"
      ? searchFiltered
      : searchFiltered.filter((crop) => crop.status === filter)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Field-scoped Context Banner & Disclosures */}
      {selectedField ? (
        <Card className="p-4 bg-primary/5 border-primary/20 space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Sprout className="w-4 h-4 text-primary" />
              <span className="font-semibold text-sm text-foreground">
                Plan & Recommendations for: <strong>{selectedField.name}</strong> ({selectedField.areaAcres} Acres)
              </span>
            </div>
            <Badge variant="outline" className="text-xs">
              {selectedField.soilType}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-primary flex-shrink-0" />
            <span>
              Soil Profile: N={selectedField.n} kg/ha · P={selectedField.p} kg/ha · K={selectedField.k} kg/ha · pH={selectedField.ph}.
              Crops marked &ldquo;In Plan&rdquo; are assigned directly to this plot.
            </span>
          </p>
        </Card>
      ) : (
        <Card className="p-3 bg-muted/30 border-border text-xs text-muted-foreground flex items-center gap-2">
          <Info className="w-3.5 h-3.5 flex-shrink-0 text-primary" />
          <span>
            Viewing farm-wide baseline recommendations. Select a specific field in the header to calibrate by soil chemistry and view field-assigned plans.
          </span>
        </Card>
      )}

      {/* Search & Season Controls */}
      <div className="flex flex-col gap-4 lg:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search crops…"
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="gap-2 bg-transparent"
            onClick={() => setFilter(filter === "in" ? "all" : "in")}
          >
            <Filter data-icon="inline-start" />
            Filter {filter !== "all" ? `(${filter})` : ""}
          </Button>
          <Button
            variant="outline"
            className="gap-2 bg-transparent"
            onClick={cycleSeason}
          >
            <Calendar data-icon="inline-start" />
            Season: {season}
          </Button>
        </div>
      </div>

      {/* Tabs with Dynamically Calibrated Counts */}
      <div className="flex flex-wrap gap-2 items-center">
        {[
          ["all", `All (${countTotal})`],
          ["in", `In Plan (${countIn})`],
          ["out", `Not in Plan (${countOut})`],
        ].map(([value, label]) => (
          <Button
            key={value}
            id={`crop-tab-${value}`}
            variant={filter === value ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(value)}
            className="transition-all"
          >
            {label}
          </Button>
        ))}
        {loading && (
          <span className="text-xs text-muted-foreground flex items-center gap-1 ml-2">
            <Loader2 className="w-3 h-3 animate-spin" /> Evaluating ML Suitability...
          </span>
        )}
      </div>

      {/* Crops List or Empty State */}
      {filteredCrops.length === 0 ? (
        <Card className="p-8 text-center space-y-3 border-dashed">
          <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mx-auto text-muted-foreground">
            <Sprout className="w-6 h-6 text-primary/70" />
          </div>
          <h3 className="font-semibold text-base text-foreground">
            {filter === "in"
              ? `No crops in ${selectedField?.name || "this field"} plan yet`
              : "No crops found"}
          </h3>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            {filter === "in"
              ? `Add crops to ${selectedField?.name || "your field"} using "+ Add Crop to Plan" above, or browse the catalogue under "Not in Plan" and check crops to assign them.`
              : "Try adjusting your search query or seasonal filter."}
          </p>
          {filter === "in" && (
            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              {onOpenAddCrop && (
                <Button
                  id="btn-empty-add-crop"
                  size="sm"
                  onClick={onOpenAddCrop}
                  className="gap-1.5 text-xs"
                >
                  <Sprout className="w-3.5 h-3.5" /> + Add Crop to Plan
                </Button>
              )}
              {countOut > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilter("out")}
                  className="text-xs"
                >
                  Browse Catalogue Crops ({countOut})
                </Button>
              )}
            </div>
          )}
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredCrops.map((crop, index) => (
            <Card
              key={`${crop.crop_id}-${crop.id}`}
              className={`
                cursor-pointer p-4 transition-all duration-300 hover:shadow-lg animate-slide-in border
                ${crop.status === "in" ? "border-primary/40 bg-primary/5" : "border-border hover:border-border/80"}
              `}
              style={{ animationDelay: `${index * 40}ms` }}
              onClick={() => toggleCropStatus(crop.id)}
            >
              <div className="flex items-start gap-4">
                <Checkbox
                  checked={crop.status === "in"}
                  aria-label={`${crop.title} included in ${selectedField?.name || "field"} plan`}
                  className="mt-1"
                  disabled={togglingCropId === crop.crop_id}
                  onCheckedChange={() => toggleCropStatus(crop.id)}
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-foreground">
                        {crop.emoji} {crop.title}
                      </h3>
                      {crop.status === "in" && (
                        <Badge variant="default" className="text-[10px] h-4.5 px-1.5 bg-primary/90">
                          In Plan {crop.acres ? `(${crop.acres} ac)` : ""}
                        </Badge>
                      )}
                    </div>
                    <Badge variant={crop.variant} className="shrink-0">
                      {crop.suitability}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Tag className="w-3.5 h-3.5" />
                      Expected yield {crop.yield}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      Sow: {crop.sow}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs">
                      Profit {crop.profit}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      Water: {crop.water}
                    </Badge>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
