import React, { useState } from 'react';
import { AlertCircle, CheckCircle, PackagePlus, Trash2, X } from 'lucide-react';
import type { ProductInventoryStatus } from '../types';

interface StockAdjustModalProps {
  product: ProductInventoryStatus | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmitAdjustment: (payload: {
    sku: string;
    adjustment_qty: number;
    adjustment_type: string;
    reason: string;
    performed_by: string;
  }) => Promise<void>;
  onSubmitAudit: (sku: string, visibleQty: number, backroomQty?: number) => Promise<void>;
}

export const StockAdjustModal: React.FC<StockAdjustModalProps> = ({
  product,
  isOpen,
  onClose,
  onSubmitAdjustment,
  onSubmitAudit,
}) => {
  const [mode, setMode] = useState<'DELIVERY' | 'SHRINKAGE' | 'AUDIT'>('DELIVERY');
  const [qty, setQty] = useState<number>(10);
  const [backroomQty, setBackroomQty] = useState<number>(product?.estimated_backroom_qty || 0);
  const [reason, setReason] = useState<string>('Supplier Delivery Restock');
  const [performedBy, setPerformedBy] = useState<string>('Store Manager');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen || !product) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      if (mode === 'AUDIT') {
        await onSubmitAudit(product.sku, qty, backroomQty);
      } else {
        const delta = mode === 'DELIVERY' ? Math.abs(qty) : -Math.abs(qty);
        const adjType = mode === 'DELIVERY' ? 'DELIVERY' : 'SHRINKAGE_WRITEOFF';
        await onSubmitAdjustment({
          sku: product.sku,
          adjustment_qty: delta,
          adjustment_type: adjType,
          reason: reason || (mode === 'DELIVERY' ? 'Replenishment delivery' : 'Damaged / expired write-off'),
          performed_by: performedBy,
        });
      }
      onClose();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Operation failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-lg glass-panel bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white">Stock Adjustment & Shelf Audit</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {product.name} ({product.sku})
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current State Summary */}
        <div className="grid grid-cols-3 gap-2 my-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
          <div>
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Visible Shelf</span>
            <p className="text-base font-bold text-emerald-400">{product.visible_shelf_qty} pcs</p>
          </div>
          <div>
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Backroom Est.</span>
            <p className="text-base font-bold text-blue-400">{product.estimated_backroom_qty} pcs</p>
          </div>
          <div>
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Book Total</span>
            <p className="text-base font-bold text-cyan-400">{product.book_inventory_qty} pcs</p>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex p-1 rounded-xl bg-slate-950/80 border border-slate-800 mb-4">
          <button
            type="button"
            onClick={() => {
              setMode('DELIVERY');
              setReason('Supplier Delivery Restock');
              setQty(12);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition ${
              mode === 'DELIVERY'
                ? 'bg-emerald-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <PackagePlus className="w-3.5 h-3.5" />
            <span>Delivery (+)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setMode('SHRINKAGE');
              setReason('Damaged or Expired Write-Off');
              setQty(2);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition ${
              mode === 'SHRINKAGE'
                ? 'bg-rose-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Write-Off (-)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setMode('AUDIT');
              setQty(product.visible_shelf_qty);
              setBackroomQty(product.estimated_backroom_qty);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition ${
              mode === 'AUDIT'
                ? 'bg-blue-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Physical Audit</span>
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="flex items-center space-x-2 p-3 mb-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'AUDIT' ? (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Counted Visible Shelf Stock
                </label>
                <input
                  type="number"
                  min="0"
                  max={product.shelf_capacity * 2}
                  value={qty}
                  onChange={(e) => setQty(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
                <span className="text-[11px] text-slate-400">
                  Planogram max shelf facing: {product.shelf_capacity} units
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Counted Backroom Reserve (Optional)
                </label>
                <input
                  type="number"
                  min="0"
                  value={backroomQty}
                  onChange={(e) => setBackroomQty(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {mode === 'DELIVERY' ? 'Received Quantity (+)' : 'Write-Off Quantity (-)'}
                </label>
                <input
                  type="number"
                  min="1"
                  value={qty}
                  onChange={(e) => setQty(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Reason / Note</label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. PO-9481 or damaged in transit"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Performed By</label>
            <input
              type="text"
              value={performedBy}
              onChange={(e) => setPerformedBy(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl bg-slate-800 hover:bg-slate-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-5 py-2 text-xs font-semibold rounded-xl text-slate-950 transition shadow-lg active:scale-95 disabled:opacity-50 ${
                mode === 'DELIVERY'
                  ? 'bg-emerald-500 hover:bg-emerald-400 shadow-emerald-500/20'
                  : mode === 'SHRINKAGE'
                  ? 'bg-rose-500 hover:bg-rose-400 text-white shadow-rose-500/20'
                  : 'bg-blue-500 hover:bg-blue-400 text-white shadow-blue-500/20'
              }`}
            >
              {isSubmitting ? 'Updating Ledger...' : 'Commit Ledger Update'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
