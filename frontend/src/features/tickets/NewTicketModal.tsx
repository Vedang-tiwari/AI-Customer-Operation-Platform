import React, { useState } from 'react';
import { api } from '../../api/client';
import { Ticket } from '../../types';
import { Plus, X, Sparkles, Zap } from 'lucide-react';

interface NewTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTicketCreated: (ticket: Ticket) => void;
}

export const NewTicketModal: React.FC<NewTicketModalProps> = ({
  isOpen,
  onClose,
  onTicketCreated
}) => {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState('web');
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) return;

    setIsSubmitting(true);
    try {
      const ticket = await api.createTicket({
        subject,
        description,
        source,
        idempotency_key: idempotencyKey || undefined
      });
      onTicketCreated(ticket);
      onClose();
    } catch (err: any) {
      alert(err.message || 'Failed to create ticket');
    } finally {
      setIsSubmitting(false);
    }
  };

  const loadPreset = (presetSubject: string, presetDesc: string, presetSource: string) => {
    setSubject(presetSubject);
    setDescription(presetDesc);
    setSource(presetSource);
    setIdempotencyKey(`demo-${Date.now()}`);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-left">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Plus className="w-4 h-4 text-indigo-400" />
            <span>Create Support Ticket</span>
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Demo Quick Presets */}
        <div className="space-y-1.5">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Zap className="w-3 h-3 text-amber-400" /> Demo Quick Presets
          </span>
          <div className="flex flex-wrap gap-1.5 text-[11px]">
            <button
              type="button"
              onClick={() => loadPreset(
                "Duplicate subscription charge on credit card",
                "I was billed twice on my Visa for the annual plan. Please issue a refund for the extra $99.",
                "web"
              )}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-slate-300 transition"
            >
              💳 Duplicate Charge (Billing)
            </button>
            <button
              type="button"
              onClick={() => loadPreset(
                "Security Alert: Unauthorized access from foreign IP",
                "Our security scanner detected credential stuffing attempts and unauthorized API calls.",
                "api"
              )}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-600 hover:text-white text-slate-300 transition"
            >
              🚨 Security Breach (Urgent)
            </button>
            <button
              type="button"
              onClick={() => loadPreset(
                "Webhook integration returning HTTP 500 error",
                "Our production service is failing to receive payment event webhooks due to a 500 internal server error.",
                "webhook"
              )}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-blue-600 hover:text-white text-slate-300 transition"
            >
              ⚡ Webhook 500 (Technical)
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 pt-2">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              Subject
            </label>
            <input
              type="text"
              placeholder="e.g. Duplicate subscription charge"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              Channel / Source
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="web">Web Form</option>
              <option value="api">REST API</option>
              <option value="webhook">External Webhook</option>
              <option value="email">Email Adapter</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              Customer Inquiry / Description
            </label>
            <textarea
              placeholder="Describe the customer request..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              required
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 resize-none font-sans"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              Idempotency Key (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. evt-uuid-987"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition"
            >
              {isSubmitting ? 'Processing AI...' : 'Submit & Route'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
