"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Droplets, Leaf, CloudSun } from "lucide-react"

export function Reminders() {
  return (
    <Card
      className="p-6 transition-all duration-500 hover:shadow-xl animate-slide-in-up"
      style={{ animationDelay: "500ms" }}
    >
      <h2 className="text-xl font-semibold text-foreground mb-6">AI Recommendations</h2>
      <div className="space-y-4">
        <div className="bg-card border border-border rounded-xl p-4 transition-all duration-300 hover:shadow-lg hover:scale-[1.02]">
          <div className="flex items-start gap-3"><Droplets className="w-5 h-5 text-sky-600 mt-0.5" /><div><h3 className="font-semibold text-foreground mb-1">Reduce irrigation by 25%</h3><p className="text-sm text-muted-foreground">Rain expected in 2 days. Save roughly 800 kL this cycle.</p></div></div>
          <div className="flex items-start gap-3 mt-4"><Leaf className="w-5 h-5 text-emerald-600 mt-0.5" /><div><h3 className="font-semibold text-foreground mb-1">Sow onion this week</h3><p className="text-sm text-muted-foreground">Conditions are ideal for your black soil field.</p></div></div>
          <Button variant="outline" className="w-full mt-4 bg-transparent"><CloudSun className="w-4 h-4 mr-2" />View 6 recommendations</Button>
        </div>
      </div>
    </Card>
  )
}
