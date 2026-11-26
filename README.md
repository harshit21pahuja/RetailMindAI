# RetailMind AI – Smart Retail Inventory & Store Intelligence System

RetailMind AI is an AI-powered retail inventory intelligence platform for retail and grocery stores. It combines visible shelf observations (via Computer Vision / YOLO) with Point-of-Sale (POS) ledger data to detect low/out-of-stock products, uncover inventory discrepancies, forecast demand, and automate replenishment recommendations.

---

## Phase 1 Status: Foundation, Database & Core APIs ✅

Phase 1 establishes the production-grade modular backend, asynchronous database layer, Pydantic schemas, and realistic seed data for **15 prototype Indian retail SKUs** alongside **90 days of daily POS transaction history**.

### Core Architecture Components Implemented:
- **FastAPI Application**: High-throughput async gateway with lifespan management, CORS configuration, and OpenAPI `/docs`.
- **SQLAlchemy 2.0 ORM**: Dual-engine setup (Async for live FastAPI request pooling + Sync for CLI seeders & batch operations).
- **SQLite Storage**: Local zero-configuration database (`retailmind.db`), architected for seamless drop-in transition to PostgreSQL via `DATABASE_URL`.
- **Relational Domain Models**:
  - `Product`: Complete SKU master catalog (prices, wholesale costs, lead times, safety thresholds, shelf capacities, barcodes).
  - `ShelfZone`: Planogram definitions (camera ID, shelf tiers, max front-facing capacities, bounding polygon coordinates).
  - `InventorySnapshot`: The physical-vs-digital fusion ledger (Visible Shelf Stock, Book Stock, Estimated Backroom Stock, Discrepancies).
  - `SalesTransaction`: Detailed checkout POS ledger (quantities, basket sizes, timestamps, payment methods: UPI, Cash, Card).
  - `ForecastMetric`: Schema for time-series demand predictions (predicted demand, confidence intervals, model lineage).
  - `ReorderRecommendation`: Schema for dynamic replenishment (Reorder Points, Daily Run Rates, Stockout Timelines).
  - `Alert`: Operational notification dispatch (Out-of-Stock, Empty Shelf, Low Stock, Shrinkage/Discrepancy).
- **Realistic Seed Engine**:
  - 15 Core Indian grocery SKUs across Beverages, Snacks, Instant Foods, Biscuits, Dairy, and Chocolates.
  - 90 days of synthetic daily sales (~12,300 transactions) incorporating weekend rushes (Fri-Sun multipliers), realistic basket sizes, and store operating hours.
  - Initial inventory snapshot with realistic test states (e.g. Amul Butter Out-of-Stock, Sprite Shelf Restock Needed, Haldiram Bhujia Low Stock).

---

## Local Setup Instructions

### 1. Prerequisites
- Python 3.10+ (Tested with Python 3.14 on Windows)

### 2. Virtual Environment Setup
From the repository root directory:

```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# (For Linux / macOS bash: source .venv/bin/activate)
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (pre-configured for local SQLite development):
```powershell
copy .env.example .env
```

### 5. Initialize & Seed Database
Seed the 15 prototype products, shelf zones, initial inventory snapshots, active alerts, and 90 days of POS sales history:
```powershell
python -m backend.seed.seed_database
```

### 6. Run the FastAPI Server
```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 7. Run the Automated Test Suite
```powershell
pytest -v
```

---

## Phase 1 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System root metadata and API links |
| `GET` | `/api/v1/health` | Health check verifying database connectivity |
| `GET` | `/api/v1/products` | List all 15 catalog products (supports `?category=` filter) |
| `GET` | `/api/v1/products/categories` | Retrieve unique product categories |
| `GET` | `/api/v1/products/{sku}` | Retrieve product details with shelf planogram zones |
| `GET` | `/api/v1/inventory/status` | Store inventory status (Visible Shelf vs Book Stock, Fill %, Status Breakdown) |
| `GET` | `/api/v1/inventory/history/{sku}` | Historical audit snapshots for an individual SKU |
| `GET` | `/api/v1/sales/history` | Paginated POS transaction ledger |
| `GET` | `/api/v1/sales/summary` | Store-wide sales metrics (total units, revenue, transactions, days recorded) |
| `GET` | `/api/v1/sales/daily/{sku}` | Daily aggregated sales time series (ready for demand forecasting) |
| `GET` | `/api/v1/alerts/active` | Unresolved store alerts (Out of stock, Shelf empty, Low stock) |
| `PUT` | `/api/v1/alerts/{alert_id}/resolve` | Mark an operational alert as resolved |

---

## Phase 2 Status: Shelf Image Upload & YOLO Product Detection ✅

Phase 2 introduces the computer vision pipeline, accepting shelf images (JPG, JPEG, PNG), executing YOLO detection, counting visible items, generating color-coded visual annotations, and saving results locally.

### Key Vision Capabilities:
- **Modular Vision Service** (`backend/services/vision_service.py`): Decoupled detection engine supporting custom-trained `.pt` retail weights as well as pretrained validation models (`yolov8n.pt`).
- **Realism & Model Mode Metadata**: Explicitly tags inference mode as `GENERIC_PIPELINE_VALIDATION` or `CUSTOM_RETAIL_SKU` with clear disclaimers, avoiding false claims that generic COCO models can distinguish fine-grained retail brands (e.g. Coke vs. Pepsi).
- **Shelf Image Detection Endpoint** (`POST /api/v1/vision/detect-shelf`):
  - Validates image types (JPG, JPEG, PNG) and payload size limit (max 15MB).
  - Returns itemized detections (class ID, name, confidence, bounding box `x1, y1, x2, y2, width, height`).
  - Aggregates visible counts per class (`class_counts`) and total objects detected.
  - Automatically draws bounding boxes with confidence labels and color palettes.
  - Safely saves annotated images to `results/detections/<timestamp>_<filename>` and serves them publicly via `/static/detections/...`.
- **Model Info Endpoint** (`GET /api/v1/vision/model-info`): Inspects model path, active mode, confidence threshold, and provides a guide for dropping in fine-tuned weights.

---

## Testing the Vision Endpoint

### 1. Using Swagger UI Interactive Docs
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), expand `POST /api/v1/vision/detect-shelf`, click **Try it out**, upload an image, and click **Execute**.

### 2. Using cURL
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/vision/detect-shelf?conf_threshold=0.25" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_data/shelf_sample.jpg"
```

### 3. Using Python
```python
import requests

url = "http://127.0.0.1:8000/api/v1/vision/detect-shelf"
files = {"file": open("sample_data/shelf_sample.jpg", "rb")}
params = {"conf_threshold": 0.25}

response = requests.post(url, files=files, params=params)
data = response.json()

print(f"Total detected items: {data['total_detected']}")
print(f"Class breakdown: {data['class_counts']}")
print(f"Annotated image URL: {data['annotated_image_url']}")
```

### 4. How to Plug in Custom Retail YOLO Weights
1. Train or download your custom retail SKU YOLO checkpoint (e.g., `retail_best.pt`).
2. Place the file inside `backend/ml_weights/retail_best.pt`.
3. Set the environment variable in `.env`:
   ```ini
   YOLO_MODEL_PATH=backend/ml_weights/retail_best.pt
   ```
4. Restart the server. The vision service will automatically recognize the custom retail classes and switch `model_mode` to `CUSTOM_RETAIL_SKU`.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System root metadata and API links |
| `GET` | `/api/v1/health` | Health check verifying database connectivity |
| `GET` | `/api/v1/products` | List all 15 catalog products (supports `?category=` filter) |
| `GET` | `/api/v1/products/categories` | Retrieve unique product categories |
| `GET` | `/api/v1/products/{sku}` | Retrieve product details with shelf planogram zones |
| `GET` | `/api/v1/inventory/status` | Store inventory status (Visible Shelf vs Book Stock, Fill %, Status Breakdown) |
| `GET` | `/api/v1/inventory/history/{sku}` | Historical audit snapshots for an individual SKU |
| `GET` | `/api/v1/sales/history` | Paginated POS transaction ledger |
| `GET` | `/api/v1/sales/summary` | Store-wide sales metrics (total units, revenue, transactions, days recorded) |
| `GET` | `/api/v1/sales/daily/{sku}` | Daily aggregated sales time series (ready for demand forecasting) |
| `GET` | `/api/v1/alerts/active` | Unresolved store alerts (Out of stock, Shelf empty, Low stock) |
| `PUT` | `/api/v1/alerts/{alert_id}/resolve` | Mark an operational alert as resolved |
| `POST`| `/api/v1/vision/detect-shelf` | **Upload shelf photo -> YOLO product detection, visible count & annotated image** |
| `GET` | `/api/v1/vision/model-info` | **Active YOLO model status, mode & plug-in guide** |
| `GET` | `/static/detections/{filename}` | **Serve annotated detection image files** |
| `GET` | `/api/v1/inventory/discrepancies` | **Discrepancy report (Shelf restock, shrinkage, phantom stock)** |
| `POST`| `/api/v1/inventory/adjust` | **Record delivery (+), shrinkage write-off (-), or physical count** |
| `POST`| `/api/v1/inventory/audit` | **Record physical shelf audit count for an individual SKU** |
| `POST`| `/api/v1/inventory/reconcile` | **Reconcile full store ledger across all active products** |
| `POST`| `/api/v1/inventory/fuse-vision` | **Fuse YOLO detection class counts into live inventory snapshots** |
| `GET` | `/api/v1/forecast/demand/{sku}` | **14-day demand forecast timeline with confidence intervals** |
| `GET` | `/api/v1/forecast/stockout-risks` | **All active SKUs ranked by stockout risk level** |
| `GET` | `/api/v1/forecast/reorder-recommendations` | **List computed reorder purchase recommendations** |
| `POST`| `/api/v1/forecast/generate-reorders` | **Run replenishment engine to compute purchase orders** |
| `PATCH`| `/api/v1/forecast/reorder-recommendations/{id}/status` | **Update reorder status (APPROVED / ORDERED / DISMISSED)** |
| `GET` | `/api/v1/cctv/status` | **Check CCTV & OpenCV ingestion service status** |
| `POST`| `/api/v1/cctv/analyze-video` | **Upload video -> Sample frames -> Detect peak shelf facings** |
| `POST`| `/api/v1/cctv/analyze-webcam` | **Timed live webcam capture & shelf detection analysis** |
| `GET` | `/static/samples/{filename}` | **Serve sample test media (shelf_sample.jpg, cctv_shelf_sample.mp4)** |

---

## Phase 3: Inventory Fusion Engine & Discrepancy Reconciliation ✅
- Physical-vs-digital fusion: $S_{vis}$ (Visible shelf observed via YOLO) vs $S_{book}$ (Digital POS inventory ledger) vs $S_{back} = \max(0, S_{book} - S_{vis})$.
- Automated detection of:
  - **Shelf Restock Needed**: When shelf stock is critically low or empty, but reserve stock is sitting in the backroom.
  - **Possible Shrinkage**: Discrepancies where audited physical count is less than book ledger stock ($S_{vis} + S_{back} < S_{book}$).
  - **Phantom Stock**: When digital book inventory shows positive stock, but both shelf and backroom are completely depleted.

---

## Phase 4: ML Demand Forecasting & Dynamic Reorder Optimizer ✅
- **Hybrid Time Series Engine**: Blended Exponential Smoothing (EMA 60%) and Weighted Moving Average (WMA 40%) trained on 90 days of POS sales history.
- **Prediction Intervals**: 80% confidence interval bands computed using demand coefficient of variation (CV).
- **Dynamic Reorder Calculation**:
  $$\text{Reorder Point (ROP)} = (\text{Daily Run Rate} \times \text{Lead Time Days}) + \text{Safety Stock}$$
- Multi-tier stockout risk classification (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `NONE`).

---

## Phase 5: CCTV Stream Video Ingestion & Monitoring ✅
- Frame-sampling pipeline extracting keyframes at configurable intervals (default: 5 seconds).
- Peak visible count aggregation across all analyzed frames.
- OpenCV 5.0.0 integration with automatic video format validation (`.mp4`, `.avi`, `.webm`, `.mov`).

---

## Phase 6: Store Owner Dashboard (React 19 + TypeScript + Vite + Tailwind CSS) ✅

The modern responsive store owner intelligence web application is built with React 19, TypeScript, Lucide React, Recharts, and Tailwind CSS.

### Running the Full System Locally:

#### 1. Start the FastAPI Backend:
```powershell
.\.venv\Scripts\python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

#### 2. Start the React Frontend Dashboard:
In a new terminal window:
```powershell
cd frontend
npm run dev
```
Open **[http://localhost:5173/](http://localhost:5173/)** in your browser. All API requests are automatically proxied to `http://127.0.0.1:8000`.

### Key Dashboard Modules:
1. **Overview Dashboard**: Store KPIs (Inventory value, shelf fill rate, active operational alerts, 90-day revenue) and actionable discrepancy summaries.
2. **Inventory & Shelf Fusion**: Live 15-SKU ledger matrix displaying visible shelf counts vs planogram capacities with fill meters, backroom reserve estimates, and one-click stock adjustment / audit modals.
3. **AI Vision & CCTV Scanner**: Drag-and-drop shelf image and video upload, YOLO confidence threshold adjustment, bounding-box detection visualization, and one-click "Fuse into Inventory" action.
4. **Demand & Reorder Hub**: Interactive 14-day Recharts demand forecasts, stockout risk radar, and purchase order workflow (Approve / Order / Dismiss).
5. **POS Sales Analytics**: 30-day velocity curves, basket size stats, payment method breakdown (UPI, Card, Cash), and live checkout transaction feed.
6. **Active Operational Alerts**: Immediate alert queue for empty shelves, low stock, and shrinkage with single-click resolution.

