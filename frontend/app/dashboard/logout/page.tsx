"use client"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { useAuth } from "@/components/auth/AuthProvider"

export default function LogoutPage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const firstName = user?.name?.split(" ")[0] || "User"

  const handleLogout = () => {
    logout()
    router.push("/")
    router.refresh()
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header title="Logout" description={`Are you sure you want to logout, ${firstName}?`} />

        <div className="flex items-center justify-center min-h-[calc(100vh-100px)]">
          <Card className="p-8 max-w-md w-full text-center space-y-6 animate-fade-in">
            <div className="flex justify-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <LogOut className="w-8 h-8 text-primary" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-2">Logout</h1>
              <p className="text-muted-foreground">Are you sure you want to logout, {firstName}?</p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1 bg-transparent" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button className="flex-1 bg-primary hover:bg-primary/90" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}