import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { HistoryContent } from "@/components/dashboard/dashboard/history-content"

export default function HistoryPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header title="Plan History" description="Your past season plans and how they performed." />

        <div className="mt-6">
          <HistoryContent />
        </div>
      </main>
    </div>
  )
}