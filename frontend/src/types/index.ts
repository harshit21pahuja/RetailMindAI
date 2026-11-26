export interface Product {
  sku: string;
  name: string;
  brand: string;
  category: string;
  price: number;
  unit_cost: number;
  lead_time_days: number;
  min_safety_stock: number;
  shelf_capacity: number;
  package_type: string;
  barcode?: string;
  image_url?: string;
  is_active: boolean;
}

export interface InventorySnapshotOut {
  id: number;
  sku: string;
  recorded_at: string;
  visible_shelf_qty: number;
  book_inventory_qty: number;
  estimated_backroom_qty: number;
  discrepancy_qty: number;
  audit_source: string;
  status: string;
  confidence_score: number;
}

export interface ProductInventoryStatus {
  sku: string;
  name: string;
  category: string;
  price: number;
  shelf_capacity: number;
  threshold: number;
  visible_shelf_qty: number;
  book_inventory_qty: number;
  estimated_backroom_qty: number;
  discrepancy_qty: number;
  shelf_fill_pct: number;
  inventory_value: number;
  status: 'HEALTHY' | 'LOW_STOCK' | 'OUT_OF_STOCK' | 'SHELF_RESTOCK_NEEDED' | 'POSSIBLE_SHRINKAGE' | 'PHANTOM_STOCK' | 'DISCREPANCY' | string;
  brand?: string;
  image_url?: string;
  last_checked?: string;
  last_audit_time?: string;
}

export interface InventoryOverviewResponse {
  total_skus: number;
  healthy_count: number;
  low_stock_count: number;
  out_of_stock_count: number;
  restock_needed_count: number;
  shrinkage_count: number;
  phantom_stock_count: number;
  discrepancy_count: number;
  inventory_value: number;
  items: ProductInventoryStatus[];
}

export interface DiscrepancyItem {
  sku: string;
  name: string;
  category: string;
  discrepancy_type: 'SHELF_RESTOCK_NEEDED' | 'POSSIBLE_SHRINKAGE' | 'SHRINKAGE' | 'PHANTOM_STOCK' | string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | string;
  visible_shelf_qty: number;
  book_inventory_qty: number;
  estimated_backroom_qty: number;
  discrepancy_qty: number;
  estimated_financial_loss: number;
  explanation: string;
  recommended_action: string;
}

export interface DiscrepancyReportResponse {
  total_discrepancies: number;
  shelf_restock_count: number;
  shrinkage_count: number;
  phantom_stock_count: number;
  total_potential_loss: number;
  items: DiscrepancyItem[];
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface DetectedItem {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
}

export interface ShelfDetectionResponse {
  filename: string;
  image_width: number;
  image_height: number;
  total_detected: number;
  class_counts: Record<string, number>;
  detections: DetectedItem[];
  annotated_image_url: string;
  annotated_image_path: string;
  model_name: string;
  model_mode: string;
  disclaimer: string;
  inference_time_ms: number;
}

export interface ReconciliationResult {
  sku: string;
  product_name: string;
  old_visible_shelf_qty: number;
  new_visible_shelf_qty: number;
  book_inventory_qty: number;
  backroom_qty: number;
  discrepancy_qty: number;
  previous_status: string;
  new_status: string;
  alert_generated: boolean;
  timestamp: string;
}

export interface ForecastMetric {
  id?: number;
  sku?: string;
  forecast_date: string;
  predicted_demand: number;
  lower_bound: number;
  upper_bound: number;
  confidence_score: number;
  model_name: string;
}

export interface ProductForecastTimeline {
  sku: string;
  product_name: string;
  current_stock: number;
  daily_run_rate: number;
  days_to_depletion: number;
  forecast_points: ForecastMetric[];
}

export interface StockoutRiskItem {
  sku: string;
  product_name: string;
  category: string;
  current_stock: number;
  daily_run_rate: number;
  days_to_depletion: number;
  lead_time_days: number;
  stockout_risk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE' | string;
  risk_description: string;
  reorder_point: number;
}

export interface StockoutRisksResponse {
  total: number;
  items: StockoutRiskItem[];
}

export interface ReorderRecommendation {
  id: number;
  sku: string;
  current_stock: number;
  daily_run_rate: number;
  stockout_days_est: number;
  reorder_point: number;
  recommended_order_qty: number;
  estimated_cost: number;
  priority: 'URGENT' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE' | string;
  status: 'PENDING' | 'APPROVED' | 'ORDERED' | 'DISMISSED' | string;
  created_at: string;
}

export interface SalesSummaryResponse {
  total_transactions: number;
  total_units_sold: number;
  total_revenue: number;
  days_recorded: number;
}

export interface DailySalesAgg {
  date: string;
  sku: string;
  total_quantity: number;
  total_revenue: number;
}

export interface SalesTransaction {
  id: number;
  transaction_id: string;
  sku: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  timestamp: string;
  payment_method: string;
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  sku: string;
  title: string;
  message: string;
  is_resolved: boolean;
  created_at: string;
  updated_at: string;
}

export interface CCTVStatusResponse {
  cctv_service_available: boolean;
  opencv_version?: string;
  supported_video_formats: string[];
  max_video_size_mb: number;
  note: string;
}

export interface CCTVFrameResult {
  frame_index: number;
  timestamp_sec: number;
  timestamp_label: string;
  detections: any[];
  total_detected: number;
  counts_per_class: Record<string, number>;
  annotated_frame_path?: string | null;
  annotated_frame_url?: string | null;
}

export interface CCTVAnalysisResponse {
  session_id: string;
  source: string;
  video_path?: string;
  video_fps?: number;
  video_duration_sec: number;
  total_video_frames?: number;
  frames_sampled: number;
  frames_analyzed?: number;
  sample_interval_sec: number;
  max_frames_cap?: number;
  processed_at: string;
  frame_results: CCTVFrameResult[];
  aggregated_counts: Record<string, number>;
  peak_visible_counts?: Record<string, number>;
  aggregated_total: number;
  original_filename?: string;
  caveat: string;
}
