"use client";

import React, { useState } from 'react';
import { Shield, Zap, Lock, ArrowRight, BarChart3, Users } from 'lucide-react';
import AuthModal from './AuthModal';

export default function LandingPage() {
  const [showAuth, setShowAuth] = useState(false);

  return (
    <div className="landing-container animate-fade-in">
      {/* Navigation */}
      <nav className="nav-glass">
        <div className="nav-content">
          <div className="logo flex-center">
            <BarChart3 className="text-primary mr-2" />
            <span className="logo-text">FINA</span>
          </div>
          <button
            onClick={() => setShowAuth(true)}
            className="btn-primary"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <div className="badge animate-fade-in">
            <span className="badge-dot"></span>
            Agentic Finance is Here
          </div>
          <h1 className="hero-title gradient-text">
            Orchestrate Your <br /> Financial Future
          </h1>
          <p className="hero-subtitle">
            Experience the power of Agentic AI. Multi-agent orchestration,
            HITL governance, and ephemeral RAG for ultimate privacy.
          </p>
          <div className="hero-actions">
            <button onClick={() => setShowAuth(true)} className="btn-primary-large">
              Get Started <ArrowRight className="ml-2 h-5 w-5" />
            </button>
            <button className="btn-secondary-large">
              View Methodology
            </button>
          </div>
        </div>

        {/* Abstract Background Elements */}
        <div className="hero-visual">
          <div className="glow-sphere"></div>
          <div className="glass-card-preview animate-float">
            <div className="card-line w-full"></div>
            <div className="card-line w-2/3"></div>
            <div className="card-line w-1/2"></div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features">
        <div className="section-header">
          <h2 className="section-title">Privacy by Design</h2>
          <p className="section-subtitle">0-Cost infrastructure, 0-Data persistence. Your documents are ephemeral.</p>
        </div>

        <div className="features-grid">
          <FeatureCard
            icon={<Shield className="text-primary" />}
            title="Ephemeral RAG"
            description="Your documents are indexed in a temporary memory and deleted permanently upon logout."
          />
          <FeatureCard
            icon={<Lock className="text-secondary" />}
            title="HITL Governance"
            description="Advanced human-in-the-loop protocols for high-stakes financial recommendations."
          />
          <FeatureCard
            icon={<Zap className="text-accent" />}
            title="Multi-Agent Flow"
            description="Autonomous agents investigating, reasoning and orchestrating portfolio tasks."
          />
        </div>
      </section>

      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      <style jsx>{`
        .landing-container {
          min-height: 100vh;
          background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.05), transparent),
                      radial-gradient(circle at bottom left, rgba(139, 92, 246, 0.05), transparent);
        }

        .nav-glass {
          position: fixed;
          top: 0;
          width: 100%;
          z-index: 50;
          background: rgba(5, 7, 10, 0.6);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .nav-content {
          max-width: 1200px;
          margin: 0 auto;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .logo-text {
          font-family: 'Outfit', sans-serif;
          font-weight: 700;
          font-size: 1.5rem;
          letter-spacing: -0.02em;
        }

        .hero {
          padding: 10rem 2rem 5rem;
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1.2fr 0.8fr;
          gap: 4rem;
          align-items: center;
        }

        .hero-title {
          font-size: 4.5rem;
          line-height: 1.1;
          margin-bottom: 1.5rem;
          letter-spacing: -0.04em;
        }

        .hero-subtitle {
          font-size: 1.25rem;
          color: var(--text-muted);
          max-width: 600px;
          margin-bottom: 2.5rem;
          line-height: 1.6;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.2);
          padding: 0.5rem 1rem;
          border-radius: 99px;
          font-size: 0.875rem;
          color: var(--primary);
          margin-bottom: 2rem;
        }

        .badge-dot {
          width: 6px;
          height: 6px;
          background: var(--primary);
          border-radius: 50%;
          margin-right: 0.75rem;
          box-shadow: 0 0 10px var(--primary);
        }

        .btn-primary {
          background: var(--primary);
          color: white;
          padding: 0.6rem 1.5rem;
          border-radius: 8px;
          font-weight: 600;
          transition: var(--transition);
          border: none;
          cursor: pointer;
        }

        .btn-primary:hover {
          filter: brightness(1.1);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px var(--primary-glow);
        }

        .btn-primary-large {
          background: var(--primary);
          color: white;
          padding: 1rem 2rem;
          border-radius: 12px;
          font-weight: 600;
          font-size: 1.1rem;
          display: flex;
          align-items: center;
          transition: var(--transition);
          border: none;
          cursor: pointer;
        }

        .btn-secondary-large {
          background: rgba(255, 255, 255, 0.05);
          color: white;
          padding: 1rem 2rem;
          border-radius: 12px;
          font-weight: 600;
          font-size: 1.1rem;
          transition: var(--transition);
          border: 1px solid rgba(255, 255, 255, 0.1);
          cursor: pointer;
        }

        .hero-actions {
          display: flex;
          gap: 1rem;
        }

        .hero-visual {
          position: relative;
          height: 400px;
        }

        .glow-sphere {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 300px;
          height: 300px;
          background: var(--primary);
          filter: blur(100px);
          opacity: 0.2;
          border-radius: 50%;
        }

        .glass-card-preview {
          position: absolute;
          width: 280px;
          height: 360px;
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          padding: 2rem;
          top: 20px;
          left: 40px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .card-line {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          margin-bottom: 1.5rem;
        }

        .features {
          padding: 5rem 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .section-header {
          text-align: center;
          margin-bottom: 4rem;
        }

        .section-title {
          font-size: 2.5rem;
          margin-bottom: 1rem;
        }

        .section-subtitle {
          color: var(--text-muted);
          font-size: 1.1rem;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2rem;
        }

        @keyframes float {
          0% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
          100% { transform: translateY(0px); }
        }

        .animate-float {
          animation: float 6s ease-in-out infinite;
        }

        @media (max-width: 1024px) {
          .hero {
            grid-template-columns: 1fr;
            text-align: center;
            padding-top: 8rem;
          }
          .hero-content {
            display: flex;
            flex-direction: column;
            align-items: center;
          }
          .hero-visual {
            display: none;
          }
          .features-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="glass-card p-8">
      <div className="icon-container mb-6 flex-center h-12 w-12 rounded-xl bg-white/5 border border-white/10">
        {icon}
      </div>
      <h3 className="text-xl mb-3">{title}</h3>
      <p className="text-muted leading-relaxed">
        {description}
      </p>
      <style jsx>{`
        .text-muted {
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
