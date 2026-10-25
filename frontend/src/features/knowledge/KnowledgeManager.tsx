import React, { useState, useEffect } from 'react';
import { KnowledgeDocument } from '../../types';
import { api } from '../../api/client';
import { BookOpen, Upload, Search, FileText, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';

interface KnowledgeManagerProps {
  documents: KnowledgeDocument[];
  onRefresh: () => void;
}

export const KnowledgeManager: React.FC<KnowledgeManagerProps> = ({
  documents,
  onRefresh
}) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // Semantic query test
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setIsUploading(true);
    try {
      await api.uploadDocument(title, content);
      setTitle('');
      setContent('');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const results = await api.searchKnowledge(searchQuery);
      setSearchResults(results);
    } catch (err: any) {
      alert(err.message || 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 text-left max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-400" />
          <span>Knowledge Base & Semantic RAG</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Ingest company policies, SLA agreements, and product documentation into pgvector-compatible semantic embeddings.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="lg:col-span-1 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Upload className="w-4 h-4 text-indigo-400" />
            <span>Ingest Document</span>
          </h3>

          <form onSubmit={handleUpload} className="space-y-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                Document Title
              </label>
              <input
                type="text"
                placeholder="e.g., Enterprise SLA Guarantee"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                Document Content (Markdown/Text)
              </label>
              <textarea
                placeholder="Paste authorized policy paragraphs here..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={8}
                required
                className="w-full p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
              />
            </div>

            <button
              type="submit"
              disabled={isUploading}
              className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isUploading ? 'Chunking & Embedding...' : 'Index Document'}</span>
            </button>
          </form>
        </div>

        {/* Document List & Query Tester */}
        <div className="lg:col-span-2 space-y-6">
          {/* Query Tester */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Search className="w-4 h-4 text-indigo-400" />
              <span>Semantic Retrieval Playground</span>
            </h3>

            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                placeholder="Test a customer inquiry (e.g. 'Can I get a refund for double charge?')..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={isSearching}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="text-[11px] font-semibold text-slate-400">
                  Matching Passages ({searchResults.length}):
                </div>
                {searchResults.map((res, i) => (
                  <div
                    key={res.chunk_id || i}
                    className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between text-[11px] text-indigo-400 font-mono">
                      <span>Source: {res.document_title || res.chunk_id}</span>
                      <span className="text-emerald-400 font-bold">
                        Score: {Math.round(res.similarity * 100)}%
                      </span>
                    </div>
                    <p className="text-slate-300 italic">"{res.content}"</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Indexed Documents Table */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              <span>Authorized Organization Documents ({documents.length})</span>
            </h3>

            <div className="divide-y divide-slate-800/80">
              {documents.length === 0 ? (
                <div className="text-xs text-slate-500 py-4">No documents indexed yet.</div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="py-3 flex items-center justify-between">
                    <div className="space-y-0.5">
                      <div className="text-xs font-semibold text-slate-200">{doc.title}</div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        ID: {doc.id} • v{doc.version} • {doc.file_type}
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      doc.status === 'indexed'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
