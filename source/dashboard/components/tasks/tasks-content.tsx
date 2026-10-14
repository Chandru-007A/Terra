"use client"

import { useState } from "react"
import { Calendar, Filter, Search, Tag } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"

const crops = [
  { id: 1, emoji: "🧅", title: "Onion (Rabi)", suitability: "92% Highly Suitable", status: "in", yield: "90 q/acre", sow: "Oct 25 – Nov 15", profit: "₹74,000/acre", water: "High", variant: "default" as const },
  { id: 2, emoji: "🫘", title: "Chickpea (Gram)", suitability: "88% Highly Suitable", status: "in", yield: "8 q/acre", sow: "Oct 15 – Nov 10", profit: "₹30,400/acre", water: "Low", variant: "default" as const },
  { id: 3, emoji: "🌾", title: "Wheat (Rabi)", suitability: "81% Suitable", status: "in", yield: "18 q/acre", sow: "Nov 1 – Nov 25", profit: "₹23,000/acre", water: "Medium", variant: "secondary" as const },
  { id: 4, emoji: "🌼", title: "Mustard (Rabi)", suitability: "67% Moderate", status: "in", yield: "7 q/acre", sow: "Oct 10 – Oct 31", profit: "₹21,500/acre", water: "Low", variant: "outline" as const },
  { id: 5, emoji: "🌿", title: "Sorghum (Rabi Jowar)", suitability: "63% Moderate", status: "out", yield: "9 q/acre", sow: "Oct 1 – Oct 20", profit: "₹12,000/acre", water: "Low", variant: "outline" as const },
  { id: 6, emoji: "🟡", title: "Safflower", suitability: "58% Moderate", status: "out", yield: "6 q/acre", sow: "Oct 5 – Nov 5", profit: "₹14,500/acre", water: "Low", variant: "outline" as const },
]

export function TasksContent() {
  const [filter, setFilter] = useState("all")
  const filteredCrops = filter === "all" ? crops : crops.filter((crop) => crop.status === filter)
  return <div className="space-y-6 animate-fade-in">
    <div className="flex flex-col gap-4 lg:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><Input placeholder="Search crops…" className="pl-10" /></div><div className="flex gap-2"><Button variant="outline" className="gap-2 bg-transparent"><Filter data-icon="inline-start" />Filter</Button><Button variant="outline" className="gap-2 bg-transparent"><Calendar data-icon="inline-start" />Season</Button></div></div>
    <div className="flex flex-wrap gap-2">{[["all", "All (6)"], ["in", "In Plan (4)"], ["out", "Not in Plan (2)"]].map(([value, label]) => <Button key={value} variant={filter === value ? "default" : "outline"} size="sm" onClick={() => setFilter(value)}>{label}</Button>)}</div>
    <div className="grid gap-4">{filteredCrops.map((crop, index) => <Card key={crop.id} className="cursor-pointer p-4 transition-all duration-300 hover:shadow-lg animate-slide-in" style={{ animationDelay: `${index * 50}ms` }}><div className="flex items-start gap-4"><Checkbox checked={crop.status === "in"} aria-label={`${crop.title} included in optimized plan`} className="mt-1" /><div className="min-w-0 flex-1 space-y-2"><div className="flex items-start justify-between gap-4"><h3 className="font-semibold text-foreground">{crop.emoji} {crop.title}</h3><Badge variant={crop.variant} className="shrink-0">{crop.suitability}</Badge></div><div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground"><span className="flex items-center gap-1"><Tag />Expected yield {crop.yield}</span><span className="flex items-center gap-1"><Calendar />Sow: {crop.sow}</span></div><div className="flex flex-wrap gap-2"><Badge variant="outline" className="text-xs">Profit {crop.profit}</Badge><Badge variant="outline" className="text-xs">Water: {crop.water}</Badge></div></div></div></Card>)}</div>
  </div>
}
