import React, { useState } from 'react';
import {
  AlertCircle,
  AlertOctagon,
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock,
  Filter,
} from 'lucide-react';
import type { Alert } from '../types';

interface AlertsTabProps {
  alerts: Alert[];
  onResolveAlert: (id: number) => Promise<void>;
  isResolving?: boolean;
}

export const AlertsTab: React.FC<AlertsTabProps> = ({
  alerts,
  onResolveAlert,
}) => {
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter === 'ALL') return true;
    return a.severity === severityFilter;
  });

  const handleResolve = async (id: number) => {
    setResolvingId(id);
    try {
      await onResolveAlert(id);
    } finally {
      setResolvingId(null);
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return {
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
          border: 'border-rose-500/30',
          icon: AlertOctagon,
          iconColor: 'text-rose-400',
        };
      case 'HIGH':
        return {
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          border: 'border-amber-500/30',
          icon: AlertTriangle,
          iconColor: 'text-amber-400',
        };
      default:
        return {
          badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
          border: 'border-blue-500/30',
          icon: AlertCircle,
          iconColor: 'text-blue-400',
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Bell className="w-5 h-5 text-rose-400 animate-pulse" />
            <span>Store Operations & Aisle Alert Stream</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Active incidents requiring floor restock, supplier escalation, or inventory adjustment
          </p>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-transparent text-xs text-white font-semibold focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-slate-900 text-white">All Alerts ({alerts.length})</option>
            <option value="CRITICAL" className="bg-slate-900 text-white">Critical</option>
            <option value="HIGH" className="bg-slate-900 text-white">High</option>
            <option value="MEDIUM" className="bg-slate-900 text-white">Medium</option>
          </select>
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="space-y-3">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => {
            const style = getSeverityStyle(alert.severity);
            const Icon = style.icon;
            const isThisResolving = resolvingId === alert.id;

            return (
              <div
                key={alert.id}
                className={`glass-panel p-5 rounded-2xl border ${style.border} transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="flex items-start space-x-3.5">
                    <div className={`p-2.5 rounded-xl bg-slate-900 border border-slate-800 ${style.iconColor} flex-shrink-0 mt-0.5`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${style.badge}`}>
                          {alert.severity}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {alert.sku}
                        </span>
                        <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            {new Date(alert.created_at).toLocaleTimeString('en-IN', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-white mt-1.5">{alert.title}</h3>
                      <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{alert.message}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleResolve(alert.id)}
                    disabled={isThisResolving}
                    className="self-end sm:self-center px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 transition shadow-sm active:scale-95 disabled:opacity-50 flex items-center space-x-1.5 flex-shrink-0"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{isThisResolving ? 'Resolving...' : 'Mark Resolved'}</span>
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white">All Clear — No Active Operational Alerts</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Visible shelves are stocked according to planogram thresholds, and POS ledger matches expectations.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
