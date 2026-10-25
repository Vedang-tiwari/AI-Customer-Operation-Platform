import React, { useState } from 'react';
import { ResponseDraft, Ticket } from '../../types';
import {
  Sparkles,
  CheckCircle,
  XCircle,
  Send,
  Edit3,
  BookOpen,
  AlertCircle,
  FileCheck2,
  RefreshCw
} from 'lucide-react';

interface ApprovalCardProps {
  draft: ResponseDraft;
  ticket: Ticket;
  onApprove: (draftId: string) => Promise<void>;
  onReject: (draftId: string, reason: string) => Promise<void>;
  onSend: (draftId: string) => Promise<void>;
  onEdit: (draftId: string, body: string) => Promise<void>;
  onRegenerate: () => Promise<void>;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  draft,
  ticket,
  onApprove,
  onReject,
  onSend,
  onEdit,
  onRegenerate
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedBody, setEditedBody] = useState(draft.body);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveEdit = async () => {
    setIsSubmitting(true);
    try {
      await onEdit(draft.id, editedBody);
      setIsEditing(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await onApprove(draft.id);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason) return;
    setIsSubmitting(true);
    try {
      await onReject(draft.id, rejectReason);
      setShowRejectModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSend = async () => {
    setIsSubmitting(true);
    try {
      await onSend(draft.id);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-100 flex items-center gap-2">
              AI Grounded Draft Suggestion
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                {draft.created_by_model}
              </span>
            </h4>
          </div>
        </div>

        {/* Confidence Meter & Status */}
        <div className="flex items-center gap-2">
          {draft.confidence_score !== undefined && (
            <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500">Confidence:</span>
              <span className="font-semibold text-emerald-400">
                {Math.round(draft.confidence_score * 100)}%
              </span>
            </div>
          )}

          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg uppercase tracking-wide border ${
            draft.status === 'approved'
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : draft.status === 'rejected'
              ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
              : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
          }`}>
            {draft.status}
          </span>
        </div>
      </div>

      {/* Draft Body Content */}
      {isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editedBody}
            onChange={(e) => setEditedBody(e.target.value)}
            rows={8}
            className="w-full p-3 rounded-xl bg-slate-950 border border-indigo-500/50 text-xs text-slate-200 focus:outline-none font-sans leading-relaxed"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 text-xs hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveEdit}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              Save Draft
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
          {draft.body}
        </div>
      )}

      {/* Citations Section */}
      {draft.citations && draft.citations.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800/60">
          <div className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
            <span>Verified Knowledge Citations ({draft.citations.length})</span>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {draft.citations.map((cit, idx) => (
              <div
                key={cit.id || idx}
                className="bg-slate-950/60 border border-slate-800 rounded-lg p-2.5 text-left text-[11px]"
              >
                <div className="flex items-center justify-between text-[10px] text-indigo-400 font-mono mb-1">
                  <span>Source Chunk: {cit.chunk_id}</span>
                  {cit.relevance_score && (
                    <span className="text-slate-500">
                      Similarity: {Math.round(cit.relevance_score * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-slate-400 italic font-serif">
                  "{cit.passage_snippet || 'Verified knowledge reference passage.'}"
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Human Review Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800">
        <div className="flex items-center gap-2">
          {draft.status === 'draft' && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Draft</span>
            </button>
          )}

          <button
            onClick={onRegenerate}
            disabled={isSubmitting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Regenerate</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {draft.status === 'draft' && (
            <>
              <button
                onClick={() => setShowRejectModal(true)}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
              <button
                onClick={handleApprove}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Approve Draft</span>
              </button>
            </>
          )}

          {draft.status === 'approved' && ticket.status !== 'sent' && ticket.status !== 'resolved' && (
            <button
              onClick={handleSend}
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition transform active:scale-95"
            >
              <Send className="w-4 h-4" />
              <span>Authorize & Deliver Response</span>
            </button>
          )}

          {draft.status === 'rejected' && (
            <div className="text-xs text-rose-400 font-medium">
              Rejected: {draft.rejection_reason || 'Needs revision'}
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>Reject AI Suggestion</span>
            </h3>
            <p className="text-xs text-slate-400">
              Please state why this draft is being rejected so the model and team can adjust triage.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g., Inaccurate policy cited, customer tier requires custom exception..."
              rows={3}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={!rejectReason || isSubmitting}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
