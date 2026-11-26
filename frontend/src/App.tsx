import { useCallback, useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewTab } from './components/OverviewTab';
import { InventoryTab } from './components/InventoryTab';
import { VisionTab } from './components/VisionTab';
import { ForecastTab } from './components/ForecastTab';
import { SalesAnalyticsTab } from './components/SalesAnalyticsTab';
import { AlertsTab } from './components/AlertsTab';
import { ErrorBoundary } from './components/ErrorBoundary';
import { api } from './services/api';
import type {
  Alert,
  DiscrepancyReportResponse,
  InventoryOverviewResponse,
  SalesSummaryResponse,
} from './types';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('forecast');
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isReconciling, setIsReconciling] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Core Data States
  const [inventory, setInventory] = useState<InventoryOverviewResponse | null>(null);
  const [discrepancies, setDiscrepancies] = useState<DiscrepancyReportResponse | null>(null);
  const [salesSummary, setSalesSummary] = useState<SalesSummaryResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // 1. Health check
      try {
        await api.checkHealth();
        setIsBackendHealthy(true);
      } catch {
        setIsBackendHealthy(false);
      }

      // 2. Parallel data fetch
      const [invData, discData, salesData, alertsData] = await Promise.allSettled([
        api.getInventoryStatus(),
        api.getDiscrepancies(),
        api.getSalesSummary(),
        api.getActiveAlerts(),
      ]);

      if (invData.status === 'fulfilled') setInventory(invData.value);
      if (discData.status === 'fulfilled') setDiscrepancies(discData.value);
      if (salesData.status === 'fulfilled') setSalesSummary(salesData.value);
      if (alertsData.status === 'fulfilled') setAlerts(alertsData.value);
    } catch (err: any) {
      console.error('Data sync failed:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const handleTriggerReconciliation = async () => {
    setIsReconciling(true);
    try {
      const results = await api.reconcileStore();
      showToast(`Store reconciled: ${results.length} SKUs processed across visible & book ledgers.`);
      await loadAllData();
    } catch {
      showToast('Store reconciliation failed', 'error');
    } finally {
      setIsReconciling(false);
    }
  };

  const handleResolveAlert = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      showToast('Alert resolved successfully.');
    } catch {
      showToast('Failed to resolve alert', 'error');
    }
  };

  const handleAdjustStock = async (payload: any) => {
    await api.adjustStock(payload);
    showToast(`Stock adjustment recorded for SKU ${payload.sku}`);
  };

  const handleAuditShelf = async (sku: string, visibleQty: number, backroomQty?: number) => {
    await api.auditShelf(sku, visibleQty, backroomQty);
    showToast(`Shelf audit recorded: ${visibleQty} units visible for ${sku}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeAlertCount={alerts.length}
        isBackendHealthy={isBackendHealthy}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
      />

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-2 px-4 py-3 rounded-2xl glass-panel bg-slate-900/95 border border-slate-700 shadow-2xl animate-bounce">
          {toastMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-400" />
          )}
          <span className="text-xs font-semibold text-white">{toastMessage.text}</span>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {!isBackendHealthy && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <span>
                Backend server is currently disconnected or booting up at <code>http://127.0.0.1:8000</code>.
                Make sure the FastAPI backend is running!
              </span>
            </div>
            <button
              onClick={loadAllData}
              className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-bold"
            >
              Retry Connection
            </button>
          </div>
        )}

        <ErrorBoundary>
          {activeTab === 'overview' && (
            <OverviewTab
              inventory={inventory}
              discrepancies={discrepancies}
              salesSummary={salesSummary}
              onNavigateTab={setActiveTab}
              onTriggerReconciliation={handleTriggerReconciliation}
              isReconciling={isReconciling}
            />
          )}

          {activeTab === 'inventory' && (
            <InventoryTab
              inventory={inventory}
              onRefresh={loadAllData}
              onTriggerReconciliation={handleTriggerReconciliation}
              isReconciling={isReconciling}
              onAdjustStock={handleAdjustStock}
              onAuditShelf={handleAuditShelf}
            />
          )}

          {activeTab === 'vision' && (
            <VisionTab onInventoryUpdated={loadAllData} />
          )}

          {activeTab === 'forecast' && (
            <ForecastTab
              products={inventory?.items || []}
              onRefreshInventory={loadAllData}
            />
          )}

          {activeTab === 'sales' && (
            <SalesAnalyticsTab
              products={inventory?.items || []}
              salesSummary={salesSummary}
            />
          )}

          {activeTab === 'alerts' && (
            <AlertsTab
              alerts={alerts}
              onResolveAlert={handleResolveAlert}
            />
          )}
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-300">RetailMind AI</span>
            <span>•</span>
            <span>Shelf Computer Vision & Inventory Intelligence</span>
          </div>
          <p className="text-slate-400">
            Phase 1–6 Architecture: YOLOv8 + FastAPI + SQLite + React 19 + Recharts + Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
