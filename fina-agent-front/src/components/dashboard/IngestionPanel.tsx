"use client";

import React, { useState, useRef } from 'react';
import { FileUp, FileText, CheckCircle2, AlertCircle, X, Loader2, ShieldCheck } from 'lucide-react';
import { apiService } from '@/services/api';

interface UploadingFile {
    file: File;
    progress: number;
    status: 'idle' | 'uploading' | 'success' | 'error';
    error?: string;
}

export default function IngestionPanel() {
    const [files, setFiles] = useState<UploadingFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFiles = Array.from(e.dataTransfer.files);
        processFiles(droppedFiles);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            processFiles(Array.from(e.target.files));
        }
    };

    const processFiles = (newFiles: File[]) => {
        // Basic validation
        const validExtensions = ['.pdf', '.txt', '.docx'];
        const maxSizeBytes = 50 * 1024 * 1024; // 50MB

        const validFiles = newFiles.filter(f => {
            const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
            return validExtensions.includes(ext) && f.size <= maxSizeBytes;
        }).map(f => ({
            file: f,
            progress: 0,
            status: 'idle' as const
        }));

        setFiles(prev => [...prev, ...validFiles]);
    };

    const uploadFile = async (index: number) => {
        const fileToUpload = files[index];
        if (fileToUpload.status === 'success') return;

        // Update status to uploading
        updateFileStatus(index, { status: 'uploading' });

        try {
            await apiService.uploadFile(fileToUpload.file);
            updateFileStatus(index, { status: 'success' });
        } catch (err: any) {
            updateFileStatus(index, { status: 'error', error: err.message });
        }
    };

    const updateFileStatus = (index: number, updates: Partial<UploadingFile>) => {
        setFiles(prev => prev.map((f, i) => i === index ? { ...f, ...updates } : f));
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    return (
        <div className="ingestion-container animate-fade-in">
            <div className="panel-header">
                <h2 className="gradient-text text-3xl mb-2">Knowledge Base</h2>
                <p className="text-muted">Upload financial documents to enhance your personal agent's context.</p>
            </div>

            <div className="ingestion-layout">
                <div className="upload-section">
                    <div
                        className={`drop-zone glass-card ${isDragging ? 'dragging' : ''}`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            multiple
                            hidden
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            accept=".pdf,.txt,.docx"
                        />
                        <div className="flex-center flex-col p-12">
                            <div className="icon-glow mb-6">
                                <FileUp size={48} className="text-primary" />
                            </div>
                            <h3 className="text-xl mb-2">Drop documents here</h3>
                            <p className="text-muted text-sm">PDF, TXT or DOCX (Max 50MB)</p>
                        </div>
                    </div>

                    <div className="privacy-badge glass-panel mt-6 flex items-center p-4">
                        <ShieldCheck size={24} className="text-secondary mr-3" />
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-secondary">Privacy Guaranteed</p>
                            <p className="text-sm text-muted">Files are stored in ephemeral memory and deleted on logout.</p>
                        </div>
                    </div>
                </div>

                <div className="file-list-section">
                    <h4 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Selected Files ({files.length})</h4>

                    {files.length === 0 ? (
                        <div className="empty-list flex-center flex-col py-20 glass-card">
                            <FileText size={32} className="text-muted/30 mb-3" />
                            <p className="text-muted text-sm">No files selected yet</p>
                        </div>
                    ) : (
                        <div className="file-grid">
                            {files.map((fileObj, idx) => (
                                <div key={idx} className="file-item glass-panel">
                                    <div className="file-info">
                                        <FileText size={20} className="text-primary" />
                                        <div className="ml-3 overflow-hidden">
                                            <p className="file-name truncate text-sm font-medium">{fileObj.file.name}</p>
                                            <p className="file-size text-xs text-muted">{(fileObj.file.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    </div>

                                    <div className="file-actions">
                                        {fileObj.status === 'idle' && (
                                            <button onClick={() => uploadFile(idx)} className="action-btn" style={{ color: 'var(--primary)', opacity: 1 }}>
                                                Upload
                                            </button>
                                        )}
                                        {fileObj.status === 'uploading' && (
                                            <Loader2 size={18} className="animate-spin text-primary" />
                                        )}
                                        {fileObj.status === 'success' && (
                                            <CheckCircle2 size={18} style={{ color: '#10b981' }} />
                                        )}
                                        {fileObj.status === 'error' && (
                                            <div className="flex items-center group relative">
                                                <AlertCircle size={18} style={{ color: '#ef4444' }} />
                                                <span className="error-tooltip">{fileObj.error}</span>
                                            </div>
                                        )}
                                        <button onClick={() => removeFile(idx)} className="icon-btn-small">
                                            <X size={16} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
        .ingestion-container {
          padding: 2rem;
          height: 100%;
          overflow-y: auto;
        }

        .panel-header {
          margin-bottom: 3rem;
        }

        .ingestion-layout {
          display: grid;
          grid-template-columns: 1fr 1.5fr;
          gap: 3rem;
        }

        .drop-zone {
          cursor: pointer;
          transition: var(--transition);
          border-style: dashed;
        }

        .drop-zone:hover, .drop-zone.dragging {
          border-color: var(--primary);
          background: rgba(59, 130, 246, 0.05);
        }

        .icon-glow {
          position: relative;
        }

        .icon-glow::after {
          content: '';
          position: absolute;
          inset: -10px;
          background: var(--primary);
          filter: blur(20px);
          opacity: 0.2;
          z-index: -1;
        }

        .file-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem;
          margin-bottom: 1rem;
        }

        .file-info {
          display: flex;
          align-items: center;
          flex: 1;
        }

        .file-actions {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .action-btn {
          background: none;
          border: none;
          font-weight: 600;
          font-size: 0.85rem;
          cursor: pointer;
        }

        .icon-btn-small {
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: var(--transition);
        }

        .icon-btn-small:hover {
          color: #ef4444;
        }

        .error-tooltip {
          position: absolute;
          bottom: 100%;
          right: 0;
          background: #ef4444;
          color: white;
          padding: 0.5rem;
          border-radius: 6px;
          font-size: 0.75rem;
          white-space: nowrap;
          display: none;
          z-index: 20;
        }

        .group:hover .error-tooltip {
          display: block;
        }

        @media (max-width: 1024px) {
          .ingestion-layout {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
        </div>
    );
}
