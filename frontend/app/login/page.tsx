"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { Eye, EyeOff, Loader2, CheckCircle, AlertCircle, Leaf, Sprout, BarChart3, Droplets } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/components/auth/AuthProvider"

// Feature highlights shown in the left panel
const features = [
  { icon: Leaf, label: "AI Crop Recommendations" },
  { icon: BarChart3, label: "Yield Predictions" },
  { icon: Droplets, label: "Resource Optimization" },
  { icon: Sprout, label: "Farm Strategy Planning" },
]

// Carousel slides for the left panel
const slides = [
  {
    title: "Optimize Your Farm's Potential",
    desc: "AI-powered crop allocation that maximizes yield while respecting land, water, fertilizer, and budget constraints.",
  },
  {
    title: "Data-Driven Decisions",
    desc: "Use machine learning to predict yields, classify crops, and compare farming strategies in real time.",
  },
  {
    title: "Track Every Season",
    desc: "Save optimization plans, review history, and iterate on what works best for your region and soil.",
  },
]

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login, register, user } = useAuth()

  const nextPath = searchParams.get("next") || "/dashboard"

  const [activeTab, setActiveTab] = useState("signin")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [village, setVillage] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const [slideIndex, setSlideIndex] = useState(0)

  // Auto-advance carousel
  useEffect(() => {
    const timer = setInterval(() => {
      setSlideIndex((i) => (i + 1) % slides.length)
    }, 4000)
    return () => clearInterval(timer)
  }, [])

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      router.push(nextPath)
    }
  }, [user, router, nextPath])

  if (user) {
    return (
      <div className="min-h-screen bg-[#0B0C0F] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#4CAF82]" />
      </div>
    )
  }

  const validateEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")

    if (!validateEmail(email)) {
      setError("Invalid email address")
      return
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    setLoading(true)
    const result = await login(email, password)
    setLoading(false)

    if ("error" in result) {
      setError(result.error)
    } else {
      router.push(nextPath)
      router.refresh()
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")

    if (!name.trim()) {
      setError("Name is required")
      return
    }
    if (!validateEmail(email)) {
      setError("Invalid email address")
      return
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    setLoading(true)
    const result = await register({ name, email, password, village })
    setLoading(false)

    if ("error" in result) {
      setError(result.error)
    } else {
      setSuccess("Account created successfully! Redirecting...")
      setTimeout(() => {
        router.push(nextPath)
        router.refresh()
      }, 1000)
    }
  }

  const fillDemoCredentials = () => {
    setEmail("ramesh.patil@gmail.com")
    setPassword("terra123")
    setActiveTab("signin")
    setError("")
    setSuccess("")
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* ── LEFT PANEL ── */}
      <div className="relative hidden lg:flex flex-col items-center justify-center p-10 bg-[#1A2B22] text-white overflow-hidden">
        {/* Background image with overlay */}
        <div className="absolute inset-0">
          <Image
            src="/hero-fields.png"
            alt="Agricultural fields"
            fill
            className="object-cover opacity-25"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-br from-[#1A2B22]/90 via-[#1A2B22]/70 to-[#0d4a2a]/80" />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-md mx-auto text-center space-y-8">
          {/* Brand */}
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-9 h-9 rounded-xl bg-[#4CAF82] flex items-center justify-center shadow-lg">
              <Sprout className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">TERRA</span>
          </div>

          {/* Carousel slide */}
          <div className="space-y-4 min-h-[100px]">
            <h2 className="text-2xl font-semibold leading-snug text-white">
              {slides[slideIndex].title}
            </h2>
            <p className="text-sm text-white/70 leading-relaxed">
              {slides[slideIndex].desc}
            </p>
          </div>

          {/* Dot indicators */}
          <div className="flex justify-center gap-2">
            {slides.map((_, i) => (
              <button
                key={i}
                onClick={() => setSlideIndex(i)}
                className={`transition-all duration-300 rounded-full ${
                  i === slideIndex
                    ? "w-6 h-2 bg-[#4CAF82]"
                    : "w-2 h-2 bg-white/30 hover:bg-white/50"
                }`}
                aria-label={`Go to slide ${i + 1}`}
              />
            ))}
          </div>

          {/* Feature badges */}
          <div className="grid grid-cols-2 gap-3 pt-4">
            {features.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10 text-sm text-white/80"
              >
                <Icon className="w-4 h-4 text-[#4CAF82] flex-shrink-0" />
                <span>{label}</span>
              </div>
            ))}
          </div>

          {/* Demo hint */}
          <p className="text-xs text-white/40 pt-2">
            Demo: ramesh.patil@gmail.com / terra123
          </p>
        </div>
      </div>

      {/* ── RIGHT PANEL ── */}
      <div className="flex flex-col items-center justify-center p-8 bg-white dark:bg-[#0B0C0F] min-h-screen">
        <div className="w-full max-w-sm space-y-6">

          {/* Mobile brand header */}
          <div className="flex lg:hidden items-center justify-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-[#4CAF82] flex items-center justify-center">
              <Sprout className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">TERRA</span>
          </div>

          {/* Heading */}
          <div className="text-center">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">
              {activeTab === "signin" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {activeTab === "signin"
                ? "Sign in to access your farm dashboard"
                : "Join TERRA to optimize your crops and resources"}
            </p>
          </div>

          {/* Alerts */}
          {error && (
            <div
              className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-400"
              role="alert"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div
              className="flex items-center gap-2 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-400"
              role="status"
            >
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              {success}
            </div>
          )}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="w-full grid grid-cols-2 mb-4 bg-gray-100 dark:bg-white/5 rounded-lg p-1">
              <TabsTrigger
                value="signin"
                className="rounded-md text-sm data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-white/10 dark:data-[state=active]:text-white text-gray-500 dark:text-gray-400"
              >
                Sign in
              </TabsTrigger>
              <TabsTrigger
                value="register"
                className="rounded-md text-sm data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-white/10 dark:data-[state=active]:text-white text-gray-500 dark:text-gray-400"
              >
                Create account
              </TabsTrigger>
            </TabsList>

            {/* ── Sign In Form ── */}
            <TabsContent value="signin" className="space-y-4">
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                    disabled={loading}
                    autoComplete="email"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pr-10 border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                      disabled={loading}
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-[#4CAF82] hover:bg-[#3d9e72] text-white font-medium py-2.5 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
                  disabled={loading}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Signing in...
                    </span>
                  ) : (
                    "Sign in"
                  )}
                </Button>
              </form>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200 dark:border-white/10" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-2 bg-white dark:bg-[#0B0C0F] text-gray-400">or</span>
                </div>
              </div>

              <p className="text-center text-xs text-gray-400 dark:text-gray-500">
                Use demo account:{" "}
                <button
                  onClick={fillDemoCredentials}
                  className="text-[#4CAF82] hover:underline font-medium"
                >
                  ramesh.patil@gmail.com / terra123
                </button>
              </p>
            </TabsContent>

            {/* ── Register Form ── */}
            <TabsContent value="register" className="space-y-4">
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="name" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Full Name
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ramesh Patil"
                    className="w-full border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                    disabled={loading}
                    autoComplete="name"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="email-reg" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Email
                  </Label>
                  <Input
                    id="email-reg"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                    disabled={loading}
                    autoComplete="email"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="village" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Village <span className="text-gray-400 font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="village"
                    type="text"
                    value={village}
                    onChange={(e) => setVillage(e.target.value)}
                    placeholder="Nashik"
                    className="w-full border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                    disabled={loading}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="password-reg" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="password-reg"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pr-10 border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                      disabled={loading}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Confirm Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pr-10 border-gray-300 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-gray-500 focus:border-[#4CAF82] focus:ring-[#4CAF82]/20"
                      disabled={loading}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                      aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-[#4CAF82] hover:bg-[#3d9e72] text-white font-medium py-2.5 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
                  disabled={loading}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating account...
                    </span>
                  ) : (
                    "Create account"
                  )}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          {/* Back link */}
          <p className="text-center text-xs text-gray-400 dark:text-gray-500">
            <Link
              href="/"
              className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors inline-flex items-center gap-1"
            >
              ← Back to home
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-white dark:bg-[#0B0C0F] flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-[#4CAF82]" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  )
}