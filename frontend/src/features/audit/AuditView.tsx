import React from 'react';
import { AuditEvent } from '../../types';
import { ShieldCheck, Clock, User, Tag } from 'lucide-react';

interface AuditViewProps {
  events: AuditEvent[];
  isLoading: boolean;
}

export const AuditView: React.FC<AuditViewProps> = ({ events, isLoading }) => {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 text-left max-w-5xl mx-auto">
      <div>
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <span>Immutable Audit Trail & Compliance</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Audited record of all approvals, ticket state mutations, deliveries, and security events.
        </p>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
        {isLoading ? (
          <div className="text-center text-xs text-slate-500 py-8">Loading audit events...</div>
        ) : events.length === 0 ? (
          <div className="text-center text-xs text-slate-500 py-8">No audit events recorded yet.</div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {events.map((evt) => (
              <div key={evt.id} className="py-3.5 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {evt.action}
                    </span>
                    <span className="text-slate-300 font-medium">
                      Target: <span className="font-mono text-slate-400">{evt.target_type} #{evt.target_id.slice(0, 8)}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(evt.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    <span>Actor: {evt.actor_email || 'System Background Worker'}</span>
                  </div>
                  {evt.details && Object.keys(evt.details).length > 0 && (
                    <span className="text-[10px] font-mono text-slate-500 max-w-md truncate">
                      {JSON.stringify(evt.details)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
