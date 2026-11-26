import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Boxes,
  CheckCircle2,
  Edit3,
  Filter,
  PackageCheck,
  RefreshCw,
  Search,
} from 'lucide-react';
import type { InventoryOverviewResponse, ProductInventoryStatus } from '../types';
import { StockAdjustModal } from './StockAdjustModal';

interface InventoryTabProps {
  inventory: InventoryOverviewResponse | null;
  onRefresh: () => void;
  onTriggerReconciliation: () => void;
  isReconciling: boolean;
  onAdjustStock: (payload: any) => Promise<void>;
  onAuditShelf: (sku: string, visibleQty: number, backroomQty?: number) => Promise<void>;
}

export const InventoryTab: React.FC<InventoryTabProps> = ({
  inventory,
  onRefresh,
  onTriggerReconciliation,
  isReconciling,
  onAdjustStock,
  onAuditShelf,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedProduct, setSelectedProduct] = useState<ProductInventoryStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const categories = Array.from(new Set(inventory?.items.map((i) => i.category) || []));

  const filteredItems = (inventory?.items || []).filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'ALL' || item.category === categoryFilter;
    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'DISCREPANCY'
        ? ['SHELF_RESTOCK_NEEDED', 'POSSIBLE_SHRINKAGE', 'SHRINKAGE', 'PHANTOM_STOCK', 'DISCREPANCY'].includes(item.status)
        : item.status === statusFilter);
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>Healthy</span>
          </span>
        );
      case 'SHELF_RESTOCK_NEEDED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Boxes className="w-3 h-3" />
            <span>Restock Needed</span>
          </span>
        );
      case 'LOW_STOCK':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" />
            <span>Low Stock</span>
          </span>
        );
      case 'OUT_OF_STOCK':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            <span>Out of Stock</span>
          </span>
        );
      case 'POSSIBLE_SHRINKAGE':
      case 'SHRINKAGE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-500/15 text-red-300 border border-red-500/30">
            <AlertTriangle className="w-3 h-3" />
            <span>Shrinkage Suspect</span>
          </span>
        );
      case 'PHANTOM_STOCK':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <AlertCircle className="w-3 h-3" />
            <span>Phantom Stock</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-800 text-slate-300">
            <span>{status.replace(/_/g, ' ')}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <PackageCheck className="w-5 h-5 text-emerald-400" />
            <span>Visible Shelf vs Digital Ledger Matrix</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Physical visibility observed via YOLO/audits reconciled with Point-of-Sale book stock
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onTriggerReconciliation}
            disabled={isReconciling}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-md shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isReconciling ? 'animate-spin' : ''}`} />
            <span>{isReconciling ? 'Reconciling...' : 'Run Auto Reconcile'}</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-3 border border-slate-800">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by SKU or product name (e.g. Coke, Amul, Maggi)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/80 border border-slate-700/70 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Category Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-950/80 border border-slate-700/70 rounded-xl px-2.5 py-1">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer pr-1"
            >
              <option value="ALL" className="bg-slate-900 text-white">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c} className="bg-slate-900 text-white">
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-1.5 bg-slate-950/80 border border-slate-700/70 rounded-xl px-2.5 py-1">
            <span className="text-[11px] text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer pr-1"
            >
              <option value="ALL" className="bg-slate-900 text-white">All Statuses</option>
              <option value="HEALTHY" className="bg-slate-900 text-white">Healthy</option>
              <option value="SHELF_RESTOCK_NEEDED" className="bg-slate-900 text-white">Restock Needed</option>
              <option value="LOW_STOCK" className="bg-slate-900 text-white">Low Stock</option>
              <option value="OUT_OF_STOCK" className="bg-slate-900 text-white">Out of Stock</option>
              <option value="DISCREPANCY" className="bg-slate-900 text-white">Any Discrepancy</option>
            </select>
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3 px-4">Product / SKU</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Visible Shelf (vs Cap)</th>
                <th className="py-3 px-4">Backroom Est.</th>
                <th className="py-3 px-4">Book Stock</th>
                <th className="py-3 px-4">Discrepancy</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200 font-medium">
              {filteredItems.map((item) => {
                const fillPct = Math.min(100, Math.round((item.visible_shelf_qty / Math.max(1, item.shelf_capacity)) * 100));
                return (
                  <tr key={item.sku} className="hover:bg-slate-900/40 transition">
                    {/* SKU & Name */}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-3">
                        {item.image_url ? (
                          <img
                            src={item.image_url}
                            alt={item.name}
                            className="w-10 h-10 rounded-lg object-cover bg-slate-800 border border-slate-700/80 flex-shrink-0 shadow-sm"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0">
                            <PackageCheck className="w-5 h-5 text-slate-500" />
                          </div>
                        )}
                        <div>
                          <div className="font-bold text-white text-xs">{item.name}</div>
                          <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                            {item.sku} • ₹{item.price} {item.brand ? `• ${item.brand}` : ''}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                        {item.category}
                      </span>
                    </td>

                    {/* Visible Shelf & Fill Progress */}
                    <td className="py-3 px-4">
                      <div className="w-36">
                        <div className="flex items-center justify-between text-[11px] mb-1 font-semibold">
                          <span className={item.visible_shelf_qty === 0 ? 'text-rose-400' : 'text-emerald-400'}>
                            {item.visible_shelf_qty} units
                          </span>
                          <span className="text-slate-400 font-normal">/ {item.shelf_capacity} cap</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              fillPct > 50
                                ? 'bg-emerald-500'
                                : fillPct > 20
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${fillPct}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Backroom */}
                    <td className="py-3 px-4 font-mono text-blue-400">
                      {item.estimated_backroom_qty}
                    </td>

                    {/* Digital Book Stock */}
                    <td className="py-3 px-4 font-mono font-bold text-slate-100">
                      {item.book_inventory_qty}
                    </td>

                    {/* Discrepancy */}
                    <td className="py-3 px-4">
                      {item.discrepancy_qty !== 0 ? (
                        <span
                          className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] ${
                            item.discrepancy_qty < 0
                              ? 'bg-rose-500/20 text-rose-300'
                              : 'bg-purple-500/20 text-purple-300'
                          }`}
                        >
                          {item.discrepancy_qty > 0 ? `+${item.discrepancy_qty}` : item.discrepancy_qty}
                        </span>
                      ) : (
                        <span className="text-slate-600 font-mono text-[11px]">0</span>
                      )}
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-4">{getStatusBadge(item.status)}</td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedProduct(item);
                          setIsModalOpen(true);
                        }}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Adjust</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Adjustment Modal */}
      {selectedProduct && (
        <StockAdjustModal
          product={selectedProduct}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedProduct(null);
          }}
          onSubmitAdjustment={async (payload) => {
            await onAdjustStock(payload);
            onRefresh();
          }}
          onSubmitAudit={async (sku, vis, back) => {
            await onAuditShelf(sku, vis, back);
            onRefresh();
          }}
        />
      )}
    </div>
  );
};
