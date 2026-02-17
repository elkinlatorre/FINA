"use client";

import LandingPage from "@/components/landing/LandingPage";
import Dashboard from "@/components/dashboard/Dashboard";
import { useAuth } from "@/hooks/useAuth";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex-center h-screen bg-bg-dark">
        <div className="logo-icon animate-pulse gradient-bg">F</div>
      </div>
    );
  }

  return (
    <main>
      {user ? <Dashboard /> : <LandingPage />}
    </main>
  );
}
