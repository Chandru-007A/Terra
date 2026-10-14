import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { SettingsContent } from "@/components/dashboard/settings/settings-content"

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header title="Farm Settings" description="Manage your farm profile, preferences, and application settings." />

        <div className="mt-6">
          <SettingsContent />
        </div>
      </main>
    </div>
  )
}