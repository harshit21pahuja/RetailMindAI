import axios from 'axios';
import type {
  Alert,
  CCTVAnalysisResponse,
  CCTVStatusResponse,
  DailySalesAgg,
  DiscrepancyReportResponse,
  InventoryOverviewResponse,
  InventorySnapshotOut,
  Product,
  ProductForecastTimeline,
  ReconciliationResult,
  ReorderRecommendation,
  SalesSummaryResponse,
  SalesTransaction,
  ShelfDetectionResponse,
  StockoutRiskItem,
  StockoutRisksResponse,
} from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Products
  getProducts: async (category?: string) => {
    const params = category ? { category } : {};
    const res = await apiClient.get<Product[]>('/products', { params });
    return res.data;
  },
  getCategories: async () => {
    const res = await apiClient.get<string[]>('/products/categories');
    return res.data;
  },
  getProduct: async (sku: string) => {
    const res = await apiClient.get<Product>(`/products/${sku}`);
    return res.data;
  },

  // Inventory & Fusion
  getInventoryStatus: async () => {
    const res = await apiClient.get<InventoryOverviewResponse>('/inventory/status');
    return res.data;
  },
  getDiscrepancies: async () => {
    const res = await apiClient.get<DiscrepancyReportResponse>('/inventory/discrepancies');
    return res.data;
  },
  getInventoryHistory: async (sku?: string, limit = 50) => {
    const params: Record<string, string | number> = { limit };
    if (sku) params.sku = sku;
    const res = await apiClient.get<InventorySnapshotOut[]>('/inventory/history', { params });
    return res.data;
  },
  auditShelf: async (sku: string, visibleQty: number, backroomQty?: number) => {
    const res = await apiClient.post<ReconciliationResult>('/inventory/audit', {
      sku,
      visible_shelf_qty: visibleQty,
      audited_backroom_qty: backroomQty,
      audit_source: 'MANUAL_COUNT',
    });
    return res.data;
  },
  adjustStock: async (payload: {
    sku: string;
    adjustment_qty: number;
    adjustment_type: string;
    reason: string;
    performed_by?: string;
  }) => {
    const res = await apiClient.post('/inventory/adjust', payload);
    return res.data;
  },
  reconcileStore: async () => {
    const res = await apiClient.post<ReconciliationResult[]>('/inventory/reconcile');
    return res.data;
  },
  fuseVisionCounts: async (classCounts: Record<string, number>, zoneCode?: string) => {
    const res = await apiClient.post<ReconciliationResult[]>('/inventory/fuse-vision', {
      class_counts: classCounts,
      zone_code: zoneCode,
    });
    return res.data;
  },

  // Vision & YOLO
  detectShelf: async (file: File, confThreshold = 0.25) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<ShelfDetectionResponse>(
      `/vision/detect-shelf?conf_threshold=${confThreshold}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return res.data;
  },
  getVisionModelInfo: async () => {
    const res = await apiClient.get('/vision/model-info');
    return res.data;
  },

  // Forecast & Reorder
  getDemandForecast: async (sku: string, horizonDays = 14) => {
    const res = await apiClient.get<ProductForecastTimeline>(`/forecast/demand/${sku}`, {
      params: { horizon_days: horizonDays },
    });
    return res.data;
  },
  getStockoutRisks: async (): Promise<StockoutRiskItem[]> => {
    const res = await apiClient.get<StockoutRisksResponse | StockoutRiskItem[]>('/forecast/stockout-risks');
    if (res.data && typeof res.data === 'object' && 'items' in res.data && Array.isArray(res.data.items)) {
      return res.data.items;
    }
    if (Array.isArray(res.data)) {
      return res.data;
    }
    return [];
  },
  getReorderRecommendations: async (): Promise<ReorderRecommendation[]> => {
    const res = await apiClient.get<ReorderRecommendation[]>('/forecast/reorder-recommendations');
    if (Array.isArray(res.data)) {
      return res.data;
    }
    return [];
  },
  generateReorders: async (): Promise<ReorderRecommendation[]> => {
    const res = await apiClient.post<any>('/forecast/generate-reorders');
    if (res.data && typeof res.data === 'object' && Array.isArray(res.data.recommendations)) {
      return res.data.recommendations;
    }
    if (Array.isArray(res.data)) {
      return res.data;
    }
    return [];
  },
  updateReorderStatus: async (id: number, status: string) => {
    const res = await apiClient.patch<ReorderRecommendation>(
      `/forecast/reorder-recommendations/${id}/status`,
      { status }
    );
    return res.data;
  },

  // Sales Analytics
  getSalesSummary: async () => {
    const res = await apiClient.get<SalesSummaryResponse>('/sales/summary');
    return res.data;
  },
  getDailySales: async (sku: string) => {
    const res = await apiClient.get<DailySalesAgg[]>(`/sales/daily/${sku}`);
    return res.data;
  },
  getSalesHistory: async (page = 1, pageSize = 20) => {
    const res = await apiClient.get<SalesTransaction[]>('/sales/history', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  // Operational Alerts
  getActiveAlerts: async () => {
    const res = await apiClient.get<Alert[]>('/alerts/active');
    return res.data;
  },
  resolveAlert: async (alertId: number) => {
    const res = await apiClient.put(`/alerts/${alertId}/resolve`, { is_resolved: true });
    return res.data;
  },

  // CCTV
  getCCTVStatus: async () => {
    const res = await apiClient.get<CCTVStatusResponse>('/cctv/status');
    return res.data;
  },
  analyzeVideo: async (
    videoFile: File,
    sampleInterval = 5.0,
    maxFrames = 50
  ): Promise<CCTVAnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('sample_interval_seconds', sampleInterval.toString());
    formData.append('max_frames', maxFrames.toString());
    const res = await apiClient.post<CCTVAnalysisResponse>('/cctv/analyze-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  loadSampleImage: async (filename: string = 'shelf_sample.jpg'): Promise<File> => {
    const urls = [
      `/static/samples/${filename}`,
      `/samples/${filename}`,
      `http://127.0.0.1:8000/static/samples/${filename}`,
    ];
    let lastError: any = null;
    for (const url of urls) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          const blob = await response.blob();
          return new File([blob], filename, { type: 'image/jpeg' });
        }
      } catch (err) {
        lastError = err;
      }
    }
    throw new Error(lastError?.message || `Failed to fetch sample image: ${filename}`);
  },
  loadSampleVideo: async (filename: string = 'cctv_shelf_sample.mp4'): Promise<File> => {
    const urls = [
      `/static/samples/${filename}`,
      `/samples/${filename}`,
      `http://127.0.0.1:8000/static/samples/${filename}`,
    ];
    let lastError: any = null;
    for (const url of urls) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          const blob = await response.blob();
          return new File([blob], filename, { type: 'video/mp4' });
        }
      } catch (err) {
        lastError = err;
      }
    }
    throw new Error(lastError?.message || `Failed to fetch sample video: ${filename}`);
  },
};
