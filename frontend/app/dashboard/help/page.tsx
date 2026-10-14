import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { HelpContent } from "@/components/dashboard/help/help-content"

export default function HelpPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header title="Help & Support" description="Get help with using TERRA and find answers to common questions." />

        <div className="mt-6">
          <HelpContent />
        </div>
      </main>
    </div>
  )
}