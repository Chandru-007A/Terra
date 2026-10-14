"use client"

import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { CalendarContent } from "@/components/dashboard/calendar/calendar-content"

export default function CalendarPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title="Crop Calendar"
          description="Plan your sowing and harvest schedule for the season."
        />

        <div className="mt-6">
          {/* Add Event button is inside CalendarContent filter bar */}
          <CalendarContent />
        </div>
      </main>
    </div>
  )
}