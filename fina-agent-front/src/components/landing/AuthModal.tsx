"use client";

import React, { useState } from 'react';
import { X, Mail, Lock, User, Github, Loader2 } from 'lucide-react';
import { supabase } from '@/services/supabase';

export default function AuthModal({ onClose }: { onClose: () => void }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName } }
        });
        if (error) throw error;
        alert("Check your email for the confirmation link!");
      }
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGithubLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'github',
    });
    if (error) setError(error.message);
  };

  return (
    <div className="modal-overlay flex-center">
      <div className="modal-content glass-panel animate-fade-in">
        <button onClick={onClose} className="close-btn">
          <X size={20} />
        </button>

        <div className="modal-header">
          <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
          <p>{isLogin ? 'Sign in to access your portfolio' : 'Join the agentic revolution'}</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form className="auth-form" onSubmit={handleAuth}>
          {!isLogin && (
            <div className="input-group">
              <User className="input-icon" size={18} />
              <input
                type="text"
                placeholder="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required={!isLogin}
              />
            </div>
          )}
          <div className="input-group">
            <Mail className="input-icon" size={18} />
            <input
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <Lock className="input-icon" size={18} />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="auth-submit btn-primary-large w-full flex-center"
            disabled={loading}
          >
            {loading ? <Loader2 className="animate-spin" /> : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        <button
          onClick={handleGithubLogin}
          className="github-auth flex-center gap-3"
        >
          <Github size={20} /> Continue with GitHub
        </button>

        <p className="auth-switch">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{' '}
          <button onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: rgba(0, 0, 0, 0.8);
          backdrop-filter: blur(8px);
          z-index: 100;
          padding: 2rem;
        }

        .modal-content {
          width: 100%;
          max-width: 440px;
          padding: 3rem;
          position: relative;
        }

        .close-btn {
          position: absolute;
          top: 1.5rem;
          right: 1.5rem;
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: var(--transition);
        }

        .close-btn:hover {
          color: white;
        }

        .modal-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        .modal-header h2 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .modal-header p {
          color: var(--text-muted);
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .input-group {
          position: relative;
        }

        .input-icon {
          position: absolute;
          left: 1rem;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
        }

        input {
          width: 100%;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 1rem 1rem 1rem 3rem;
          color: white;
          font-family: inherit;
          transition: var(--transition);
        }

        input:focus {
          outline: none;
          border-color: var(--primary);
          background: rgba(255, 255, 255, 0.08);
        }

        .auth-submit {
          margin-top: 1rem;
          width: 100%;
        }

        .divider {
          text-align: center;
          margin: 2rem 0;
          position: relative;
        }

        .divider::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 0;
          width: 100%;
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
        }

        .divider span {
          background: #0d121b;
          padding: 0 1rem;
          color: var(--text-muted);
          font-size: 0.75rem;
          position: relative;
        }

        .github-auth {
          width: 100%;
          background: white;
          color: black;
          padding: 1rem;
          border-radius: 12px;
          font-weight: 600;
          border: none;
          cursor: pointer;
          transition: var(--transition);
        }

        .github-auth:hover {
          background: #e5e5e5;
        }

        .auth-switch {
          text-align: center;
          margin-top: 2.5rem;
          color: var(--text-muted);
          font-size: 0.9rem;
        }

        .auth-switch button {
          background: none;
          border: none;
          color: var(--primary);
          font-weight: 600;
          cursor: pointer;
        }

        .w-full { width: 100%; }
        .flex-center { display: flex; align-items: center; justify-content: center; }
        .gap-3 { gap: 0.75rem; }
        .error-message {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #f87171;
          padding: 0.75rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
          font-size: 0.85rem;
          text-align: center;
        }
      `}</style>
    </div>
  );
}
