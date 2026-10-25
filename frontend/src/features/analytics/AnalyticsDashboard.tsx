import React from 'react';
import { AnalyticsOverview } from '../../types';
import {
  BarChart3,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Zap,
  TrendingUp,
  Inbox
} from 'lucide-react';

interface AnalyticsDashboardProps {
  analytics: AnalyticsOverview | null;
  isLoading: boolean;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  analytics,
  isLoading
}) => {
  if (isLoading || !analytics) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-slate-500 text-xs">
        Loading analytics metrics...
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.round(seconds / 60);
    if (mins < 60) return `${mins}m`;
    const hours = (seconds / 3600).toFixed(1);
    return `${hours}h`;
  };

  const kpis = [
    {
      title: 'Total Ticket Volume',
      value: analytics.ticket_volume,
      unit: 'tickets',
      icon: Inbox,
      color: 'text-indigo-400 bg-indigo-500/10'
    },
    {
      title: 'First-Response Time',
      value: formatDuration(analytics.first_response_time_seconds),
      unit: 'avg duration',
      icon: Clock,
      color: 'text-emerald-400 bg-emerald-500/10'
    },
    {
      title: 'Resolution Time',
      value: formatDuration(analytics.resolution_time_seconds),
      unit: 'avg duration',
      icon: CheckCircle2,
      color: 'text-blue-400 bg-blue-500/10'
    },
    {
      title: 'Escalation Rate',
      value: `${(analytics.escalation_rate * 100).toFixed(1)}%`,
      unit: 'high/urgent priority',
      icon: AlertTriangle,
      color: 'text-amber-400 bg-amber-500/10'
    },
    {
      title: 'Draft Approval Rate',
      value: `${(analytics.draft_approval_rate * 100).toFixed(1)}%`,
      unit: 'human approved',
      icon: TrendingUp,
      color: 'text-purple-400 bg-purple-500/10'
    },
    {
      title: 'AI Processing Latency',
      value: `${analytics.average_processing_latency_ms.toFixed(0)}ms`,
      unit: 'classification & draft',
      icon: Zap,
      color: 'text-pink-400 bg-pink-500/10'
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 text-left max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-400" />
          <span>Operational Analytics & Performance</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Real-time metrics calculated from database timestamps and lifecycle transitions.
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl flex items-center justify-between"
            >
              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  {kpi.title}
                </span>
                <div className="text-2xl font-black text-slate-100">
                  {kpi.value}
                </div>
                <div className="text-[10px] text-slate-500 font-medium">
                  {kpi.unit}
                </div>
              </div>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${kpi.color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Category Breakdown & Status Distributions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200">
            Tickets by Category
          </h3>
          <div className="space-y-3">
            {analytics.by_category.map((item) => {
              const pct = analytics.ticket_volume > 0
                ? Math.round((item.count / analytics.ticket_volume) * 100)
                : 0;
              return (
                <div key={item.category} className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-300 capitalize font-medium">
                    <span>{item.category}</span>
                    <span className="text-slate-400">{item.count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-indigo-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200">
            Tickets by Priority
          </h3>
          <div className="space-y-3">
            {analytics.by_priority.map((item) => {
              const pct = analytics.ticket_volume > 0
                ? Math.round((item.count / analytics.ticket_volume) * 100)
                : 0;
              const color =
                item.priority === 'urgent'
                  ? 'bg-rose-500'
                  : item.priority === 'high'
                  ? 'bg-amber-500'
                  : 'bg-indigo-500';
              return (
                <div key={item.priority} className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-300 capitalize font-medium">
                    <span>{item.priority}</span>
                    <span className="text-slate-400">{item.count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${color}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
