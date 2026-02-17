"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';
import { apiService } from '@/services/api';
import { v4 as uuidv4 } from 'uuid';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  status?: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  onPendingReview: (review: { threadId: string; summary: string }) => void;
  lastDecision: any;
}

export default function ChatInterface({ onPendingReview, lastDecision }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [threadId] = useState(uuidv4());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle HITL Decision Sync
  useEffect(() => {
    if (!lastDecision) return;

    setMessages(prev => {
      const newMessages = [...prev];
      const lastAiMsgIndex = newMessages.findLastIndex(m => m.role === 'assistant' && m.status === 'pending_review');

      if (lastAiMsgIndex !== -1) {
        // 1. Update existing message status
        newMessages[lastAiMsgIndex] = {
          ...newMessages[lastAiMsgIndex],
          status: lastDecision.status === 'approved' ? 'approved' : 'rejected',
          // If approved, the agent response might be the same or slightly different
          content: lastDecision.status === 'approved' ? (lastDecision.response || newMessages[lastAiMsgIndex].content) : newMessages[lastAiMsgIndex].content
        };

        // 2. If rejected, the agent should have a "new_agent_response". Append it.
        if (lastDecision.status === 'rejected' && lastDecision.new_agent_response) {
          newMessages.push({
            id: uuidv4(),
            role: 'assistant',
            content: lastDecision.new_agent_response,
            timestamp: new Date(),
            status: 'completed'
          });
        } else if (lastDecision.status === 'approved') {
          newMessages.push({
            id: uuidv4(),
            role: 'assistant',
            content: "✅ Recommendation successfully approved by supervisor. You can now continue the conversation.",
            timestamp: new Date(),
            status: 'completed'
          });
        }
      }
      return newMessages;
    });
  }, [lastDecision]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const assistantMessageId = uuidv4();
    let currentThinking = '';
    let currentContent = '';
    let isReviewNeeded = false;

    setMessages(prev => [...prev, {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }]);

    try {
      const stream = apiService.streamChat(userMessage.content, threadId);

      for await (const chunk of stream) {
        // 1. Thinking/Tool progress
        if (chunk.type === 'thinking' || chunk.type === 'tool') {
          currentThinking = chunk.content || `[Node: ${chunk.tool}] Agent is working...`;
        }

        // 2. Incremental Content updates
        if (chunk.type === 'answer' && chunk.content) {
          currentContent += chunk.content;
        }

        // 3. Final synchronization
        if (chunk.type === 'final') {
          if (chunk.content) {
            currentContent = chunk.content; // Absolute source of truth from backend
          }
          if (chunk.status === 'pending_review') {
            isReviewNeeded = true;
            onPendingReview({
              threadId: chunk.thread_id,
              summary: chunk.content
            });
          }
        }

        setMessages(prev => prev.map(m =>
          m.id === assistantMessageId
            ? {
              ...m,
              content: currentContent,
              thinking: chunk.type === 'final' ? '' : currentThinking,
              status: chunk.status
            }
            : m
        ));
      }
    } catch (err: any) {
      setMessages(prev => prev.map(m =>
        m.id === assistantMessageId
          ? { ...m, content: "Error: Could not reach the AI agent. Please check your connection." }
          : m
      ));
    } finally {
      setLoading(false);
    }
  };

  const lastMessage = messages[messages.length - 1];
  const isPendingApproval = lastMessage?.role === 'assistant' && lastMessage?.status === 'pending_review';

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-screen flex-center flex-col h-full opacity-60">
            <Bot size={64} className="text-primary mb-6" />
            <h2 className="text-2xl mb-2">How can I assist your portfolio today?</h2>
            <p className="text-sm">I can analyze your uploaded documents, provide market insights, or help with financial planning.</p>
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`message-wrapper ${m.role}`}>
              <div className="avatar">
                {m.role === 'user' ? <User size={18} /> : <Sparkles size={18} />}
              </div>
              <div className="message-box">
                {m.thinking && (
                  <div className="thinking-bubble">
                    <RefreshCw size={12} className="animate-spin mr-2" />
                    {m.thinking}
                  </div>
                )}
                <div className="message-content">
                  {m.status === 'pending_review' && (
                    <div className="status-banner pending flex items-center mb-3">
                      <ShieldCheck size={14} className="mr-2" />
                      GOVERNANCE REQUIRED: PENDING HUMAN APPROVAL
                    </div>
                  )}
                  {m.status === 'approved' && (
                    <div className="status-banner approved flex items-center mb-3">
                      <ShieldCheck size={14} className="mr-2" />
                      GOVERNANCE CLEAR: APPROVED BY SUPERVISOR
                    </div>
                  )}
                  {m.status === 'rejected' && (
                    <div className="status-banner rejected flex items-center mb-3">
                      <AlertCircle size={14} className="mr-2" />
                      GOVERNANCE ACTION: REJECTED BY SUPERVISOR
                    </div>
                  )}
                  {m.content || (loading && m.role === 'assistant' ? <Loader2 className="animate-spin" /> : '')}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={`chat-input-area ${isPendingApproval ? 'locked' : ''}`}>
        <form onSubmit={handleSend} className="input-glass">
          <input
            type="text"
            placeholder={isPendingApproval ? "Chat locked: Waiting for supervisor approval..." : "Ask anything about your financial documents..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || isPendingApproval}
          />
          <button type="submit" className="send-btn flex-center" disabled={loading || !input.trim() || isPendingApproval}>
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>
        <p className="input-hint">
          {isPendingApproval
            ? "This conversation involves a financial recommendation and requires expert verification."
            : "FINA uses ephemeral storage. Your session will be cleared on logout."}
        </p>
      </div>

      <style jsx>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 1rem;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .message-wrapper {
          display: flex;
          gap: 1rem;
          max-width: 85%;
          animation: fadeIn 0.3s ease-out;
        }

        .message-wrapper.user {
          flex-direction: row-reverse;
          align-self: flex-end;
        }

        .avatar {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: var(--primary);
        }

        .user .avatar {
          color: var(--secondary);
        }

        .message-box {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .message-content {
          padding: 1rem 1.25rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          font-size: 0.95rem;
          line-height: 1.5;
          white-space: pre-wrap;
        }

        .user .message-content {
          background: var(--primary);
          color: white;
          border-radius: 16px 4px 16px 16px;
        }

        .assistant .message-content {
          border-radius: 4px 16px 16px 16px;
        }

        .thinking-bubble {
          display: flex;
          align-items: center;
          font-size: 0.75rem;
          color: var(--text-muted);
          background: rgba(255, 255, 255, 0.02);
          padding: 0.25rem 0.75rem;
          border-radius: 99px;
          border: 1px solid rgba(255, 255, 255, 0.05);
          margin-bottom: 0.25rem;
        }

        .status-banner {
          font-size: 0.65rem;
          font-weight: 800;
          padding: 0.4rem 0.75rem;
          border-radius: 8px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .status-banner.pending {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
          border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .status-banner.approved {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
          border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .status-banner.rejected {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .chat-input-area.locked {
          opacity: 0.6;
          pointer-events: none;
        }

        .chat-input-area {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .input-glass {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 0.5rem 0.5rem 0.5rem 1.5rem;
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .input-glass input {
          flex: 1;
          background: none;
          border: none;
          color: white;
          font-size: 1rem;
          padding: 0.75rem 0;
        }

        .input-glass input:focus { outline: none; }

        .send-btn {
          width: 44px;
          height: 44px;
          background: var(--primary);
          color: white;
          border-radius: 12px;
          border: none;
          cursor: pointer;
          transition: var(--transition);
        }

        .send-btn:hover:not(:disabled) {
          filter: brightness(1.2);
          transform: scale(1.05);
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .input-hint {
          text-align: center;
          font-size: 0.7rem;
          color: var(--text-muted);
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(5px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
