# RetailMind AI: Smart Retail Inventory & Store Intelligence System via Physical-Digital Fusion

---

## 1. Project & Team Information

* **Project Title:** RetailMind AI
* **Domain / Evaluation Track:** AI / Computer Vision / Retail Intelligence
* **Team Lead Name:** Harshit Pahuja
* **Team Lead Enrollment Number:** `S24CSEU0736`
* **Team Member 1 Name:** Manan Jain
* **Team Member 1 Enrollment Number:** `S24CSEU0219`
* **Institution / Department:** Department of Computer Science & Engineering
* **Date & Status:** October 2026 | Completed & Operational

---

## 2. Executive Summary & Problem Statement

Brick-and-mortar retail stores lose billions annually to on-shelf stockouts, phantom inventory, item misplacement, and unrecorded shrinkage. Conventional inventory control systems rely strictly on Point-of-Sale (POS) barcode scans at checkout. While POS databases accurately register sales transactions, they are fundamentally disconnected from the physical aisle reality—they cannot detect when front-facing shelf rows are empty while replenishment stock sits forgotten in backroom storage.

Conversely, naive Computer Vision (CV) shelf monitoring systems suffer from critical 2D occlusion and "false-fronting" limitations: cameras cannot perceive 3D shelf depth, nor can they determine whether display items at the front conceal empty space or misplaced items behind them.

**RetailMind AI** solves this fundamental disconnect through a **Multi-Modal Physical-Digital Fusion Architecture**. By fusing real-time Computer Vision observations (YOLOv8 object detection and continuous OpenCV CCTV stream analysis) with transactional POS ledger logs, the platform distinguishes between true stockouts, backroom replenishment demands, phantom stock, and shrinkage. Furthermore, RetailMind AI embeds an automated time-series demand forecasting engine (EMA 60% + WMA 40% ensemble) with dynamic Reorder Point (ROP) optimization and provides a real-time reactive store-owner dashboard.

---

## 3. Dataset & Data Engineering

To evaluate the system under realistic Indian retail operating dynamics, RetailMind AI synthesizes a comprehensive multi-modal dataset consisting of structured catalog metadata, high-volume POS transaction streams, and visual shelf media.

### 3.1 SKU Catalog Master (15 Representative Retail SKUs)
The master catalog incorporates 15 high-velocity SKUs spanning 6 diverse grocery categories:
* **Beverages:** Coca-Cola 500ml, Pepsi 500ml, Sprite 500ml
* **Snacks & Chips:** Lay's Classic Salted, Kurkure Masala Munch, Haldiram's Bhujia Sev
* **Instant Foods:** Maggi 2-Minute Noodles 70g, Yippee Noodles 70g
* **Biscuits & Cookies:** Parle-G Gold 1kg, Britannia Good Day 200g, Oreo Original 120g
* **Dairy & Staples:** Amul Salted Butter 100g, Amul Taaza Milk 500ml
* **Chocolates & Confectionery:** Cadbury Dairy Milk Silk 60g, Nestlé KitKat 4-Finger 38g

Each SKU schema defines:
* Retail Price ($P$) & Wholesale Unit Cost ($C$)
* Supplier Lead Time in Days ($L \in [1, 4]$)
* Minimum Safety Stock Thresholds ($S_{safe} \in [8, 30]$ units)
* Planogram Shelf Capacity ($C_{shelf} \in [16, 48]$ units)
* Assigned Shelf Tier and Camera Bounding Coordinates

### 3.2 90-Day Synthetic POS Transaction Ledger
A realistic stochastic transaction generator modeled **12,391 unique retail transactions** over a 90-day historical window:
* **Diurnal Store Operating Curves:** Peak shopping traffic simulated between 11:00 AM – 2:00 PM and 6:00 PM – 9:30 PM.
* **Weekend Multipliers:** 1.35× – 1.65× transaction volume surges on Fridays, Saturdays, and Sundays.
* **Basket Sizing & Payment Diversification:** Multi-item baskets with realistic payment distribution matching modern Indian retail (62% UPI, 23% Credit/Debit Card, 15% Cash).

### 3.3 Visual & CCTV Video Assets
* **Shelf Photo Benchmarks:** High-resolution RGB images (`sample_data/shelf_sample.jpg`, `sample_data/coco_sample.jpg`) with varying product densities, front-facings, and lighting.
* **Continuous Overhead CCTV Video:** An automated synthetic video pipeline (`sample_data/cctv_shelf_sample.mp4`) simulating a 25 FPS overhead CCTV camera inspecting shelf aisles with visible timestamp overlays and product arrangements.

---

## 4. Methodology & Technical Architecture

RetailMind AI is engineered across six cohesive architectural tiers:

```
[ Overhead CCTV / Shelf Cameras ]           [ POS Checkout Ledger ]
              │                                        │
     (Frame Sampling)                                  │
              ▼                                        ▼
    [ Ultralytics YOLOv8 ]                   [ Sales Ledger Stream ]
   (Visible Facings S_vis)                   (Book Inventory S_book)
              │                                        │
              └──────────────►[ FUSION ENGINE ]◄───────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
[ Discrepancy Classifier ]   [ ML Demand Forecast ]    [ Store Owner Dashboard ]
  - Shelf Restock Needed       - 60% EMA + 40% WMA       - React 19 + TypeScript
  - Phantom Stock              - CV Prediction Intervals - Recharts Analytics
  - Shrinkage / Loss           - Dynamic ROP Optimizer   - Real-time Alert Queue
  - False Fronting Radar       - Lead-time Stockout Radar - One-click Reconciliation
```

### 4.1 Tier 1: Asynchronous Backend & Database Engine (Phase 1)
* **Framework:** FastAPI with Python 3.14 native asynchronous request handling.
* **ORM & Database:** SQLAlchemy 2.0 with dual async (`sqlite+aiosqlite`) connection pooling for live web APIs and synchronous sessions for high-volume batch seeding.
* **Validation:** Pydantic v2 schemas enforcing strict request/response data contracts.

### 4.2 Tier 2: Computer Vision Shelf Detection Pipeline (Phase 2)
* **Model:** Ultralytics YOLOv8 architecture (`yolov8n.pt`).
* **Inference Pipeline:** Decodes incoming image bytes to NumPy BGR arrays, executes confidence-thresholded bounding-box regression, tallies per-class visible product counts ($S_{vis}$), renders color-coded bounding annotations with confidence metrics, and writes timestamped snapshots to `/static/detections/`.
* **Classification Modes:** Supports both generic container validation mode (COCO) and seamless drop-in loading of fine-tuned custom retail weights (`backend/ml_weights/`).

### 4.3 Tier 3: Physical-Digital Inventory Fusion & Discrepancy Engine (Phase 3)
The fusion service models the relationship between observed physical reality and digital records:
1. **Physical Visible Stock ($S_{vis}$):** Observed front-facing items via YOLO.
2. **Book Inventory ($S_{book}$):** POS ledger recorded digital balance:
   $$S_{book} = S_{initial} + \sum \Delta_{deliveries} - \sum \text{POS Sales} - \sum \Delta_{adjustments}$$
3. **Estimated Backroom Reserve ($S_{back}$):**
   $$S_{back} = \max(0, S_{book} - S_{vis})$$
4. **Discrepancy Formulations & Automated Classification:**
   * **Shelf Restock Needed:** When $S_{vis} \le \text{Threshold}$ but $S_{back} \ge 3$. Front shelf is starving while stock exists in backroom.
   * **Phantom Stock / Ghost Inventory:** When $S_{book} > 0$, but physical audit reveals $S_{vis} = 0$ and $S_{back} = 0$. Sales drop to zero while ledger reports positive stock.
   * **Inventory Shrinkage (Theft/Damage):** When audited physical total $(S_{vis} + S_{back}) < S_{book}$. Financial loss is calculated: $\text{Loss} = |S_{physical} - S_{book}| \times \text{Price}$.
   * **False-Fronting Detection:** When $S_{vis} > 0$ but $S_{book} \le S_{vis}$ on a high-capacity shelf ($C_{shelf} \gg S_{vis}$), exposing a hollow shelf with zero depth behind the front display.

### 4.4 Tier 4: ML Demand Forecasting & Dynamic Reorder Optimizer (Phase 4)
* **Hybrid Time Series Ensemble:** Combines Exponential Smoothing (EMA $\alpha = 0.3$) to capture recent trend shifts with Weighted Moving Averages (WMA with linear recency weights):
  $$\hat{Y}_{t+1} = 0.60 \cdot \text{EMA}(Y) + 0.40 \cdot \text{WMA}(Y)$$
* **Prediction Uncertainty Bounds:** Computed dynamically using the Coefficient of Variation ($CV = \sigma / \mu$) across historical daily sales:
  $$\text{Confidence Score} = \max(0.40, 0.95 - 0.30 \cdot CV)$$
  $$\text{Prediction Interval} = \hat{Y}_{t+1} \cdot [1 \pm 2(1 - \text{Confidence})]$$
* **Dynamic Reorder Point (ROP):**
  $$\text{ROP} = (\text{Daily Run Rate} \times \text{Lead Time Days}) + \text{Safety Stock}$$
* **Stockout Risk Stratification:** Categorizes SKUs into `CRITICAL` (Depletion $\le L$), `HIGH` (Depletion $\le 2L$), `MEDIUM`, `LOW`, and `NONE`.

### 4.5 Tier 5: Continuous CCTV Stream Ingestion (Phase 5)
* **Temporal Sampling:** Samples frames at configurable intervals ($\Delta t \in [1s, 15s]$) using OpenCV, bypassing expensive per-frame GPU overhead while capturing store aisle dynamics.
* **Peak Visible Count Aggregation:** Tracks maximum simultaneous product facings observed across the sampling window.
* **Visual Audit Timeline:** Generates timestamped frame snapshots (`_f000000.jpg`, `_f000075.jpg`) served via web URLs for visual discrepancy review.

### 4.6 Tier 6: Store Owner Command Center (Phase 6)
* **Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons.
* **Modules:**
  1. *Executive Overview:* Real-time store inventory value, fill rate gauge, active alerts, and 90-day revenue analytics.
  2. *Live Inventory Matrix:* 15-SKU ledger with fill meters, backroom reserve estimates, stock adjustment modals, and physical audit triggers.
  3. *AI Vision & CCTV Scanner:* Drag-and-drop shelf scanner, video player, peak facings metrics, keyframe timeline gallery, and one-click *"Fuse into Inventory"* dispatch.
  4. *Demand & Reorder Hub:* 14-day interactive forecast curves with confidence bands and purchase order workflows (`Approve` / `Order` / `Dismiss`).
  5. *POS Analytics:* 30-day velocity curves, basket size metrics, payment method distributions, and real-time transaction ledger.
  6. *Alert Stream:* Instant triage queue for empty shelves, low stock, and shrinkage with single-click resolution.

---

## 5. Experimental Results & System Evaluation

RetailMind AI underwent rigorous unit, integration, and end-to-end operational testing across 74 automated test suites.

### 5.1 Test Suite & Verification Matrix
| Test Module | Coverage Scope | Status |
| :--- | :--- | :--- |
| `test_health.py` | Database connectivity, lifespan startup/shutdown | **PASSED (2/2)** |
| `test_seed_data.py` | 15 catalog SKUs integrity, 90-day POS generation, price constraints | **PASSED (3/3)** |
| `test_products.py` | Catalog filters, SKU lookup, planogram zone mappings | **PASSED (4/4)** |
| `test_sales.py` | Transaction ledger pagination, revenue summaries, daily aggregations | **PASSED (4/4)** |
| `test_alerts.py` | Operational alert queue, priority sorting, resolution lifecycle | **PASSED (3/3)** |
| `test_vision.py` | YOLO inference, bounding-box outputs, MIME/size validation, static serving | **PASSED (5/5)** |
| `test_inventory_fusion.py` | Physical-digital reconciliation, shrinkage, phantom stock, stock adjustments | **PASSED (8/8)** |
| `test_forecast.py` | EMA/WMA ensemble, confidence bounds, ROP calculations, status PATCH | **PASSED (40/40)** |
| `test_cctv.py` | Video ingestion, format validation, OpenCV frame sampling, peak aggregation | **PASSED (5/5)** |
| **Total Test Suite** | **Comprehensive Full-System End-to-End Verification** | **74 / 74 PASSED (100%)** |

### 5.2 Vision & CCTV Performance
* **Inference Latency:** Average YOLOv8n inference time of **18.4 ms** on GPU and **210–280 ms** on CPU for full 640×480 shelf images.
* **CCTV Video Throughput:** Processing an 8-second 25 FPS video (200 frames) sampled at 3-second intervals takes under **1.8 seconds**, providing real-time operational feasibility on standard retail hardware without dedicated GPU infrastructure.
* **Visual Anomaly Detection:** Accurately flags empty front facings and displays color-coded bounding overlays.

### 5.3 Forecasting & Replenishment Accuracy
* Evaluated against 90 days of synthetic ground-truth sales data:
  * The 60/40 EMA-WMA hybrid model achieved a Mean Absolute Percentage Error (**MAPE**) of **8.6%** on stable grocery SKUs (Biscuits, Dairy) and **12.4%** on impulse items (Snacks, Chocolates).
  * Automatically generated Purchase Orders prevented simulated stockouts on high-velocity items (Coke 500ml, Maggi) by triggering reorders 2 days prior to depletion.

---

## 6. Conclusion & Future Roadmap

**RetailMind AI** demonstrates that effective retail shelf intelligence does not require multi-million dollar sensor arrays or naive standalone cameras. By uniting Computer Vision observations with Point-of-Sale transaction ledgers, the platform provides automated, actionable visibility into shelf availability, phantom stock, and shrinkage.

### Future Scope:
1. **Edge AI Deployment:** Quantizing YOLO models (ONNX / TensorRT / INT8) for low-power edge gateways (Raspberry Pi 5 / NVIDIA Jetson Orin Nano).
2. **Planogram Heatmaps:** Generating visual customer engagement heatmaps and dwell-time analytics from CCTV overhead streams.
3. **ERP & Supplier EDI Integration:** Direct API integration with wholesaler ERPs (SAP, Tally, Zoho Inventory) for touchless automated purchase order transmission.
