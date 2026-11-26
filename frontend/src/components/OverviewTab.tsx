import React from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  Boxes,
  Camera,
  CheckCircle2,
  DollarSign,
  PackageCheck,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import type { DiscrepancyReportResponse, InventoryOverviewResponse, SalesSummaryResponse } from '../types';
import { StatCard } from './StatCard';

interface OverviewTabProps {
  inventory: InventoryOverviewResponse | null;
  discrepancies: DiscrepancyReportResponse | null;
  salesSummary: SalesSummaryResponse | null;
  onNavigateTab: (tab: string) => void;
  onTriggerReconciliation: () => void;
  isReconciling: boolean;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  inventory,
  discrepancies,
  salesSummary,
  onNavigateTab,
  onTriggerReconciliation,
  isReconciling,
}) => {
  // Compute overall store shelf fill rate
  const totalCapacity = inventory?.items.reduce((acc, i) => acc + i.shelf_capacity, 0) || 1;
  const totalVisibleShelf = inventory?.items.reduce((acc, i) => acc + i.visible_shelf_qty, 0) || 0;
  const storeFillRate = Math.min(100, Math.round((totalVisibleShelf / totalCapacity) * 100));

  const totalStoreValueFormatted = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(inventory?.inventory_value || 0);

  const totalSalesRevenueFormatted = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(salesSummary?.total_revenue || 0);

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/40 border border-slate-800 shadow-2xl">
        <div className="absolute right-0 top-0 -mt-12 -mr-12 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Computer Vision & POS Fusion Operational</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Store Intelligence Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Fusing visible shelf stock observed by YOLO computer vision with Point-of-Sale ledger records to eliminate stockouts, identify phantom stock, and automate demand replenishment.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              id="hero-reconcile-btn"
              onClick={onTriggerReconciliation}
              disabled={isReconciling}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isReconciling ? 'animate-spin' : ''}`} />
              <span>{isReconciling ? 'Reconciling Ledger...' : 'Reconcile Store Ledger'}</span>
            </button>
            <button
              id="hero-scan-btn"
              onClick={() => onNavigateTab('vision')}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition active:scale-95"
            >
              <Camera className="w-4 h-4 text-emerald-400" />
              <span>Scan Shelf Photo</span>
            </button>
          </div>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Inventory Value"
          value={totalStoreValueFormatted}
          subtitle={`Across ${inventory?.total_skus || 15} active catalog SKUs`}
          icon={DollarSign}
          colorScheme="emerald"
          badge={{ text: 'Book Stock', variant: 'positive' }}
        />
        <StatCard
          title="Shelf Front-Facing Fill"
          value={`${storeFillRate}%`}
          subtitle={`${totalVisibleShelf} of ${totalCapacity} max capacity visible`}
          icon={Boxes}
          colorScheme={storeFillRate > 60 ? 'emerald' : 'amber'}
          badge={{
            text: storeFillRate > 60 ? 'Optimal' : 'Low Facing',
            variant: storeFillRate > 60 ? 'positive' : 'warning',
          }}
          onClick={() => onNavigateTab('inventory')}
        />
        <StatCard
          title="Inventory Discrepancies"
          value={discrepancies?.total_discrepancies || 0}
          subtitle={`Est. Financial Risk: ₹${discrepancies?.total_potential_loss || 0}`}
          icon={AlertTriangle}
          colorScheme={(discrepancies?.total_discrepancies || 0) > 0 ? 'rose' : 'emerald'}
          badge={{
            text: `${discrepancies?.shrinkage_count || 0} Shrinkage`,
            variant: (discrepancies?.shrinkage_count || 0) > 0 ? 'negative' : 'neutral',
          }}
          onClick={() => onNavigateTab('inventory')}
        />
        <StatCard
          title="90-Day POS Revenue"
          value={totalSalesRevenueFormatted}
          subtitle={`${salesSummary?.total_units_sold.toLocaleString() || 0} total units sold`}
          icon={TrendingUp}
          colorScheme="cyan"
          badge={{ text: `${salesSummary?.days_recorded || 90}d history`, variant: 'neutral' }}
          onClick={() => onNavigateTab('sales')}
        />
      </div>

      {/* Store Shelf Health Status Distribution */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <PackageCheck className="w-5 h-5 text-emerald-400" />
              <span>SKU Operational Health Breakdown</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live status classification based on visible shelf observations and digital book stock
            </p>
          </div>
          <button
            onClick={() => onNavigateTab('inventory')}
            className="inline-flex items-center space-x-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition"
          >
            <span>View Full Shelf Matrix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Status Count Bars */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-300">Healthy</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-white mt-1">
              {inventory?.healthy_count || 0}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Adequate shelf & book stock</p>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-300">Restock Needed</span>
              <Boxes className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-white mt-1">
              {inventory?.restock_needed_count || 0}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Shelf low, units in backroom</p>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-300">Low Stock</span>
              <TrendingDown className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white mt-1">
              {inventory?.low_stock_count || 0}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Below safety threshold</p>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-300">Out of Stock</span>
              <AlertOctagon className="w-4 h-4 text-rose-400" />
            </div>
            <p className="text-2xl font-bold text-white mt-1">
              {inventory?.out_of_stock_count || 0}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">0 visible, 0 backroom</p>
          </div>

          <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-300">Discrepancy</span>
              <AlertTriangle className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-white mt-1">
              {discrepancies?.total_discrepancies || 0}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Phantom or shrinkage suspect</p>
          </div>
        </div>
      </div>

      {/* Discrepancy & Actionable Intelligence Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Discrepancies */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Actionable Discrepancies</h3>
              <p className="text-xs text-slate-400">
                Immediate warehouse and store floor tasks flagged by AI fusion
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('inventory')}
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition"
            >
              See All ({discrepancies?.items.length || 0})
            </button>
          </div>

          <div className="space-y-3">
            {discrepancies && discrepancies.items.length > 0 ? (
              discrepancies.items.slice(0, 4).map((item, idx) => (
                <div
                  key={`${item.sku}-${idx}`}
                  className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-white">{item.name}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                          {item.sku}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{item.explanation}</p>
                      <div className="mt-2 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded inline-block">
                        ⚡ {item.recommended_action}
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        item.discrepancy_type === 'SHELF_RESTOCK_NEEDED'
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      {item.discrepancy_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                No active discrepancies detected across store aisles.
              </div>
            )}
          </div>
        </div>

        {/* Feature Highlights & Direct Navigation */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white mb-1">AI Intelligence Modules</h3>
            <p className="text-xs text-slate-400 mb-4">
              Explore specialized modules for Computer Vision, CCTV, Demand Forecasting, and POS Insights
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div
                onClick={() => onNavigateTab('vision')}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-emerald-500/40 cursor-pointer transition group"
              >
                <div className="flex items-center space-x-3 mb-2">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:scale-110 transition-transform">
                    <Camera className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-emerald-300">
                    Shelf Vision & CCTV
                  </h4>
                </div>
                <p className="text-[11px] text-slate-400">
                  Upload shelf photos or CCTV streams. YOLO runs inference, returns class counts, and fuses into the live inventory ledger.
                </p>
              </div>

              <div
                onClick={() => onNavigateTab('forecast')}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition group"
              >
                <div className="flex items-center space-x-3 mb-2">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:scale-110 transition-transform">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-cyan-300">
                    Demand Forecasting
                  </h4>
                </div>
                <p className="text-[11px] text-slate-400">
                  Hybrid Exponential Smoothing & WMA 14-day demand timeline with confidence intervals and automatic reorder generation.
                </p>
              </div>

              <div
                onClick={() => onNavigateTab('inventory')}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-amber-500/40 cursor-pointer transition group"
              >
                <div className="flex items-center space-x-3 mb-2">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 group-hover:scale-110 transition-transform">
                    <Boxes className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-amber-300">
                    Stock Adjustments
                  </h4>
                </div>
                <p className="text-[11px] text-slate-400">
                  Record supplier deliveries, shrinkage write-offs, or physical counts directly to update digital book stock.
                </p>
              </div>

              <div
                onClick={() => onNavigateTab('sales')}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-purple-500/40 cursor-pointer transition group"
              >
                <div className="flex items-center space-x-3 mb-2">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:scale-110 transition-transform">
                    <DollarSign className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-purple-300">
                    POS Sales Analytics
                  </h4>
                </div>
                <p className="text-[11px] text-slate-400">
                  Analyze 90 days of transactions, top selling SKUs, and payment modes (UPI, Cash, Card) driving store revenue.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
