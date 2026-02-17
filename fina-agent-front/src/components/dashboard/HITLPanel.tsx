"use client";

import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertTriangle, CheckCircle, XCircle, ChevronRight, Activity } from 'lucide-react';

export default function HITLPanel() {
    const [activeReview, setActiveReview] = useState<any>(null); // Simplified for simulation

    // Simulate a pending review for demonstration if requested
    const simulateReview = () => {
        setActiveReview({
            id: 'REQ-4521',
            type: 'INVESTMENT_ADVICE',
            summary: 'Recommendation to rebalance portfolio: Buy 5 Units of BTC, Sell 100 Units of AAPL.',
            riskScore: 8,
            supervisorNeeded: 'SUP-9988'
        });
    };

    if (!activeReview) {
        return (
            <aside className="hitl-panel empty glass-panel">
                <div className="flex-center flex-col h-full text-center p-8 opacity-40">
                    <Activity size={40} className="mb-4 text-muted" />
                    <h3 className="text-sm font-semibold uppercase tracking-widest mb-2">Governance Console</h3>
                    <p className="text-xs">Waiting for agentic triggers...</p>
                    <button onClick={simulateReview} className="mt-8 text-xs text-primary underline">Simulate HITL Trigger</button>
                </div>
                <style jsx>{`
          .hitl-panel { width: 320px; border-radius: 24px 0 0 24px; border-right: none; }
        `}</style>
            </aside>
        );
    }

    return (
        <aside className="hitl-panel glass-panel active animate-slide-in">
            <div className="panel-header p-6 border-b border-white/5">
                <div className="flex items-center justify-between mb-2">
                    <span className="badge-critical flex items-center">
                        <ShieldCheck size={14} className="mr-1" /> Governance Required
                    </span>
                    <button onClick={() => setActiveReview(null)}><XCircle size={18} className="text-muted hover:text-white" /></button>
                </div>
                <h2 className="text-xl font-bold">HITL Simulation Case</h2>
                <p className="text-xs text-muted">Approval ID: {activeReview.id}</p>
            </div>

            <div className="p-6">
                <div className="risk-indicator glass-card mb-6 p-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-semibold">Risk Level</span>
                        <span className="text-xs font-bold text-red-400">HIGH ({activeReview.riskScore}/10)</span>
                    </div>
                    <div className="progress-bar-bg h-1 rounded-full bg-white/10">
                        <div className={`progress-bar-fill h-full rounded-full bg-red-400`} style={{ width: '80%' }}></div>
                    </div>
                </div>

                <div className="review-context glass-card p-4 text-sm leading-relaxed mb-6">
                    <p className="text-muted mb-2 font-semibold">Agent Proposal:</p>
                    "{activeReview.summary}"
                </div>

                <div className="supervisor-role glass-panel p-4 mb-8">
                    <div className="flex items-center mb-3">
                        <UserCheck size={16} className="text-primary mr-2" />
                        <span className="text-xs font-bold uppercase">Authorized Supervisor</span>
                    </div>
                    <p className="text-sm font-medium">Senior Portfolio Manager</p>
                    <p className="text-xs text-muted">Auth Code: {activeReview.supervisorNeeded}</p>
                </div>

                <div className="panel-actions grid grid-cols-2 gap-3">
                    <button className="btn-approve flex-center py-3 rounded-xl font-bold text-sm">
                        <CheckCircle size={16} className="mr-2" /> Approve
                    </button>
                    <button className="btn-reject flex-center py-3 rounded-xl font-bold text-sm">
                        <XCircle size={16} className="mr-2" /> Reject
                    </button>
                </div>
            </div>

            <style jsx>{`
        .hitl-panel { width: 380px; border-radius: 24px 0 0 24px; border-right: none; background: #080b12; }
        
        .badge-critical {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          padding: 0.25rem 0.6rem;
          border-radius: 99px;
          font-size: 0.65rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .risk-indicator { border-left: 4px solid #f87171; }

        .btn-approve {
          background: var(--secondary);
          color: white;
          border: none;
          cursor: pointer;
          transition: var(--transition);
        }

        .btn-approve:hover { filter: brightness(1.1); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }

        .btn-reject {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          border: 1px solid rgba(239, 68, 68, 0.2);
          cursor: pointer;
          transition: var(--transition);
        }

        .btn-reject:hover { background: rgba(239, 68, 68, 0.2); }

        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in { animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
      `}</style>
        </aside>
    );
}
