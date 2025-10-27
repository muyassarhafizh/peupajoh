import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Zap, Brain, BarChart3 } from "lucide-react"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-8 lg:py-12">
          {/* Left Content */}
          <div className="flex flex-col justify-center">
            <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Your Personal AI Nutrition Advisor
            </h1>
            <p className="mt-6 text-lg text-muted-foreground">
              Get personalized nutrition guidance instantly. Chat with our AI nutritionist to analyze your food intake,
              receive tailored recommendations, and achieve your health goals.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/chat">
                <Button size="lg" className="w-full bg-primary text-primary-foreground hover:bg-primary/90 sm:w-auto">
                  Start Chatting
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="w-full sm:w-auto bg-transparent">
                Learn More
              </Button>
            </div>
          </div>

          {/* Right Visual */}
          <div className="flex items-center justify-center">
            <div className="relative h-96 w-full rounded-2xl bg-gradient-to-br from-primary/20 to-secondary/20 p-8 flex items-center justify-center">
              <div className="text-center">
                <Brain className="mx-auto h-24 w-24 text-primary opacity-80" />
                <p className="mt-4 text-sm font-medium text-muted-foreground">AI-Powered Nutrition Analysis</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-t border-border bg-card py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-foreground sm:text-4xl">Why Choose Peupajoh?</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Get comprehensive nutrition insights powered by advanced AI
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-lg border border-border bg-background p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-foreground">Instant Analysis</h3>
              <p className="mt-2 text-muted-foreground">
                Get real-time nutrition analysis of your meals instantly. No waiting, no complicated forms.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-lg border border-border bg-background p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-foreground">Personalized Guidance</h3>
              <p className="mt-2 text-muted-foreground">
                Receive tailored recommendations based on your dietary preferences and health goals.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-lg border border-border bg-background p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-foreground">Track Progress</h3>
              <p className="mt-2 text-muted-foreground">
                Monitor your nutrition journey with detailed insights and actionable recommendations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-primary/5 px-8 py-16 text-center">
          <h2 className="text-3xl font-bold text-foreground">Ready to Transform Your Nutrition?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Start chatting with your AI nutritionist today and get personalized guidance.
          </p>
          <Link href="/chat" className="mt-8 inline-block">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
              Get Started Now
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-muted-foreground">© 2025 Peupajoh. All rights reserved.</p>
            <div className="flex gap-6">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Privacy
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Terms
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}
