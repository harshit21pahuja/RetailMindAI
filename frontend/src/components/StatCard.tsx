import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  colorScheme?: 'emerald' | 'amber' | 'rose' | 'blue' | 'purple' | 'cyan';
  badge?: {
    text: string;
    variant: 'positive' | 'negative' | 'neutral' | 'warning';
  };
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  colorScheme = 'emerald',
  badge,
  onClick,
}) => {
  const schemeStyles = {
    emerald: {
      border: 'hover:border-emerald-500/40',
      iconBg: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      glow: 'hover:shadow-emerald-500/10',
    },
    amber: {
      border: 'hover:border-amber-500/40',
      iconBg: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
      glow: 'hover:shadow-amber-500/10',
    },
    rose: {
      border: 'hover:border-rose-500/40',
      iconBg: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
      glow: 'hover:shadow-rose-500/10',
    },
    blue: {
      border: 'hover:border-blue-500/40',
      iconBg: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
      glow: 'hover:shadow-blue-500/10',
    },
    purple: {
      border: 'hover:border-purple-500/40',
      iconBg: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
      glow: 'hover:shadow-purple-500/10',
    },
    cyan: {
      border: 'hover:border-cyan-500/40',
      iconBg: 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20',
      glow: 'hover:shadow-cyan-500/10',
    },
  }[colorScheme];

  const badgeStyles = {
    positive: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    negative: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    neutral: 'bg-slate-700/50 text-slate-300 border-slate-600/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  }[badge?.variant || 'neutral'];

  return (
    <div
      onClick={onClick}
      className={`glass-card p-5 rounded-2xl transition-all duration-300 ${schemeStyles.border} ${
        schemeStyles.glow
      } hover:shadow-xl hover:-translate-y-0.5 relative overflow-hidden group ${
        onClick ? 'cursor-pointer' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            {title}
          </p>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-2xl font-bold tracking-tight text-white group-hover:text-emerald-300 transition-colors">
              {value}
            </h3>
            {badge && (
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeStyles}`}
              >
                {badge.text}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>

        <div className={`p-3 rounded-xl ${schemeStyles.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
