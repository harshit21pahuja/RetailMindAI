import React, { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  BarChart3,
  CreditCard,
  DollarSign,
  Package,
  RefreshCw,
  ShoppingBag,
  TrendingUp,
} from 'lucide-react';
import { api } from '../services/api';
import type { DailySalesAgg, ProductInventoryStatus, SalesSummaryResponse, SalesTransaction } from '../types';
import { StatCard } from './StatCard';

interface SalesAnalyticsTabProps {
  products: ProductInventoryStatus[];
  salesSummary: SalesSummaryResponse | null;
}

export const SalesAnalyticsTab: React.FC<SalesAnalyticsTabProps> = ({ products, salesSummary }) => {
  const [selectedSku, setSelectedSku] = useState<string>(products[0]?.sku || 'BEV-COKE-500');
  const [dailySales, setDailySales] = useState<DailySalesAgg[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<SalesTransaction[]>([]);
  const [isLoadingDaily, setIsLoadingDaily] = useState<boolean>(false);

  useEffect(() => {
    const fetchDaily = async () => {
      if (!selectedSku) return;
      setIsLoadingDaily(true);
      try {
        const data = await api.getDailySales(selectedSku);
        setDailySales(data);
      } catch (err) {
        console.error('Failed to fetch daily sales', err);
      } finally {
        setIsLoadingDaily(false);
      }
    };
    fetchDaily();
  }, [selectedSku]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.getSalesHistory(1, 15);
        setRecentTransactions(data);
      } catch (err) {
        console.error('Failed to fetch sales history', err);
      }
    };
    fetchHistory();
  }, []);

  const totalRevenueFormatted = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(salesSummary?.total_revenue || 0);

  const avgUnitsPerTx = salesSummary?.total_transactions
    ? (salesSummary.total_units_sold / salesSummary.total_transactions).toFixed(1)
    : '1.8';

  const chartData = dailySales.slice(-30).map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    units: d.total_quantity,
    revenue: Math.round(d.total_revenue),
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            <span>Point-of-Sale (POS) Sales Intelligence</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            90-day transaction history, customer basket metrics, and SKU velocity trends
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Gross Revenue"
          value={totalRevenueFormatted}
          subtitle={`Across ${salesSummary?.days_recorded || 90} business days`}
          icon={DollarSign}
          colorScheme="purple"
        />
        <StatCard
          title="Total POS Transactions"
          value={salesSummary?.total_transactions.toLocaleString() || '12,000+'}
          subtitle="Customer store checkouts"
          icon={ShoppingBag}
          colorScheme="cyan"
        />
        <StatCard
          title="Total Units Sold"
          value={salesSummary?.total_units_sold.toLocaleString() || '20,000+'}
          subtitle="Physical item scans"
          icon={Package}
          colorScheme="emerald"
        />
        <StatCard
          title="Avg Basket Size"
          value={`${avgUnitsPerTx} units`}
          subtitle="Items per retail transaction"
          icon={TrendingUp}
          colorScheme="amber"
        />
      </div>

      {/* Daily Sales Velocity Chart Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
              30-Day Sales Velocity
            </span>
            <h3 className="text-lg font-bold text-white">Daily Sold Volume (Units)</h3>
            <p className="text-xs text-slate-400">
              POS checkout frequency demonstrating weekend rush patterns
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5">
            <span className="text-xs text-slate-400 font-medium">Select SKU:</span>
            <select
              value={selectedSku}
              onChange={(e) => setSelectedSku(e.target.value)}
              className="bg-transparent text-xs text-purple-400 font-bold focus:outline-none cursor-pointer"
            >
              {products.map((p) => (
                <option key={p.sku} value={p.sku} className="bg-slate-900 text-white">
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="h-72 w-full pt-4">
          {isLoadingDaily ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              <RefreshCw className="w-5 h-5 animate-spin mr-2 text-purple-400" />
              <span>Loading POS time series...</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Bar
                  dataKey="units"
                  fill="#a855f7"
                  radius={[4, 4, 0, 0]}
                  name="Units Sold"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent POS Transactions Feed */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-emerald-400" />
              <span>Real-Time POS Checkout Feed</span>
            </h3>
            <p className="text-xs text-slate-400">
              Synchronized Point-of-Sale cash register events
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Displaying latest transactions
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-2.5 px-3">Tx ID</th>
                <th className="py-2.5 px-3">SKU</th>
                <th className="py-2.5 px-3">Quantity</th>
                <th className="py-2.5 px-3">Unit Price</th>
                <th className="py-2.5 px-3">Total Amount</th>
                <th className="py-2.5 px-3">Payment Method</th>
                <th className="py-2.5 px-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {recentTransactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-2.5 px-3 font-mono text-slate-400">{tx.transaction_id}</td>
                  <td className="py-2.5 px-3 font-bold text-white">{tx.sku}</td>
                  <td className="py-2.5 px-3 font-bold text-emerald-400">{tx.quantity}</td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono">₹{tx.unit_price}</td>
                  <td className="py-2.5 px-3 font-bold text-white font-mono">₹{tx.total_amount}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        tx.payment_method === 'UPI'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : tx.payment_method === 'CARD'
                          ? 'bg-blue-500/20 text-blue-300'
                          : 'bg-amber-500/20 text-amber-300'
                      }`}
                    >
                      {tx.payment_method}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-400 text-[11px]">
                    {new Date(tx.timestamp).toLocaleString('en-IN', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
