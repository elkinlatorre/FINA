"use client";

import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertTriangle, CheckCircle, XCircle, Activity, Loader2 } from 'lucide-react';
import { apiService } from '@/services/api';

interface HITLPanelProps {
    userId: string;
    pendingReview: { threadId: string; summary: string } | null;
    onDecision: (result?: any) => void;
}

export default function HITLPanel({ userId, pendingReview, onDecision }: HITLPanelProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAction = async (approve: boolean) => {
        if (!pendingReview || loading) return;

        setLoading(true);
        setError(null);
        try {
            const result = await apiService.approveRequest(
                pendingReview.threadId,
                approve,
                'SUP-9988', // Simulation supervisor
                userId
            );
            onDecision(result); // Clear pending review from parent and pass result
        } catch (err: any) {
            setError(err.message || 'Action failed');
        } finally {
            setLoading(false);
        }
    };

    if (!pendingReview) {
        return (
            <aside className="hitl-panel empty glass-panel">
                <div className="flex-center flex-col h-full text-center p-8 opacity-40">
                    <Activity size={40} className="mb-4 text-muted" />
                    <h3 className="text-sm font-semibold uppercase tracking-widest mb-2">Governance Console</h3>
                    <p className="text-xs">Waiting for agentic triggers...</p>
                </div>
                <style jsx>{`
          .hitl-panel { width: 320px; border-radius: 24px 0 0 24px; border-right: none; height: 100vh; background: #080b12; }
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
                    <button onClick={onDecision}><XCircle size={18} className="text-muted hover:text-white" /></button>
                </div>
                <h2 className="text-xl font-bold">Dynamic Risk Case</h2>
                <p className="text-xs text-muted font-mono">ID: {pendingReview.threadId.substring(0, 13)}...</p>
            </div>

            <div className="p-6">
                <div className="risk-indicator glass-card mb-6 p-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-semibold">Risk Level</span>
                        <span className="text-xs font-bold text-red-400">HIGH (AUTO)</span>
                    </div>
                    <div className="progress-bar-bg h-1 rounded-full bg-white/10">
                        <div className={`progress-bar-fill h-full rounded-full bg-red-400`} style={{ width: '85%' }}></div>
                    </div>
                </div>

                <div className="review-context glass-card p-4 leading-relaxed mb-6 max-h-40 overflow-y-auto">
                    <p className="text-muted mb-2 font-bold uppercase tracking-tighter" style={{ fontSize: '0.65rem' }}>Proposed Response:</p>
                    <div className="italic text-white/80" style={{ fontSize: '0.7rem' }}>
                        "{pendingReview.summary}"
                    </div>
                </div>

                <div className="supervisor-role glass-panel p-4 mb-4">
                    <div className="flex items-center mb-3">
                        <UserCheck size={16} className="text-primary mr-2" />
                        <span className="text-xs font-bold uppercase">Authorized Supervisor</span>
                    </div>
                    <p className="text-sm font-medium">Senior Portfolio Manager</p>
                    <p className="text-xs text-muted">Auth Code: SUP-9988</p>
                </div>

                {error && (
                    <div className="error-box flex items-center p-3 mb-4 rounded-lg bg-red-400/10 text-red-400 text-xs">
                        <AlertTriangle size={14} className="mr-2 shrink-0" />
                        {error}
                    </div>
                )}

                <div className="panel-actions grid grid-cols-2 gap-3">
                    <button
                        onClick={() => handleAction(true)}
                        disabled={loading}
                        className="btn-approve flex-center py-3 rounded-xl font-bold text-sm"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <><CheckCircle size={16} className="mr-2" /> Approve</>}
                    </button>
                    <button
                        onClick={() => handleAction(false)}
                        disabled={loading}
                        className="btn-reject flex-center py-3 rounded-xl font-bold text-sm"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <><XCircle size={16} className="mr-2" /> Reject</>}
                    </button>
                </div>
            </div>

            <style jsx>{`
        .hitl-panel { width: 380px; border-radius: 24px 0 0 24px; border-right: none; background: #080b12; height: 100vh; border-left: 1px solid rgba(255,255,255,0.05); }
        
        .badge-critical {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          padding: 0.35rem 0.75rem;
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

        .btn-approve:hover:not(:disabled) { filter: brightness(1.1); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }

        .btn-reject {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          border: 1px solid rgba(239, 68, 68, 0.2);
          cursor: pointer;
          transition: var(--transition);
        }

        .btn-reject:hover:not(:disabled) { background: rgba(239, 68, 68, 0.2); }
        .btn-approve:disabled, .btn-reject:disabled { opacity: 0.5; cursor: not-allowed; }

        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in { animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
      `}</style>
        </aside>
    );
}
