import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette
    BG_DARK = RGBColor(15, 23, 42)      # Slate 900
    BG_LIGHT = RGBColor(248, 250, 252)  # Slate 50
    CARD_BG = RGBColor(255, 255, 255)   # Pure White
    CARD_BORDER = RGBColor(226, 232, 240) # Slate 200
    PRIMARY = RGBColor(5, 150, 105)     # Emerald 600
    PRIMARY_LIGHT = RGBColor(16, 185, 129) # Emerald 500
    ACCENT_AMBER = RGBColor(217, 119, 6) # Amber 600
    ACCENT_INDIGO = RGBColor(79, 70, 229) # Indigo 600
    ACCENT_ROSE = RGBColor(225, 29, 72)  # Rose 600
    TEXT_MAIN = RGBColor(30, 41, 59)    # Slate 800
    TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
    TEXT_LIGHT = RGBColor(255, 255, 255) # White

    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="RETAILMIND AI"):
        # Header category
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = PRIMARY

        # Main Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.5), Inches(0.6))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = BG_DARK

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: TITLE SLIDE (Dark Theme)
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, BG_DARK)

    # Accent pill tag
    tag_card = add_card(slide1, 0.9, 1.2, 3.4, 0.45, bg_color=RGBColor(30, 41, 59), border_color=PRIMARY)
    tb_tag = slide1.shapes.add_textbox(Inches(0.9), Inches(1.22), Inches(3.4), Inches(0.4))
    tf_tag = tb_tag.text_frame
    p_tag = tf_tag.paragraphs[0]
    p_tag.alignment = PP_ALIGN.CENTER
    p_tag.text = "AI & COMPUTER VISION | RETAIL INTELLIGENCE"
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = PRIMARY_LIGHT

    # Title
    tb_t = slide1.shapes.add_textbox(Inches(0.9), Inches(1.85), Inches(11.5), Inches(1.3))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = "RetailMind AI"
    p_t.font.size = Pt(50)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_LIGHT

    # Subtitle
    tb_sub = slide1.shapes.add_textbox(Inches(0.9), Inches(3.2), Inches(11.5), Inches(0.9))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "Smart Retail Inventory & Store Intelligence System via Physical-Digital Fusion"
    p_sub.font.size = Pt(22)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)

    # Team Card
    add_card(slide1, 0.9, 4.4, 11.5, 2.3, bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    tb_team = slide1.shapes.add_textbox(Inches(1.2), Inches(4.6), Inches(10.9), Inches(1.9))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True

    p1 = tf_team.paragraphs[0]
    p1.text = "TEAM INFORMATION & PROJECT DETAILS"
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = PRIMARY_LIGHT

    p2 = tf_team.add_paragraph()
    p2.text = "• Team Lead: Harshit Pahuja (Enrollment: S24CSEU0736)"
    p2.font.size = Pt(15)
    p2.font.color.rgb = TEXT_LIGHT

    p3 = tf_team.add_paragraph()
    p3.text = "• Team Member: Manan Jain (Enrollment: S24CSEU0219)"
    p3.font.size = Pt(15)
    p3.font.color.rgb = TEXT_LIGHT

    p4 = tf_team.add_paragraph()
    p4.text = "• Department: Department of Computer Science & Engineering | Status: Completed & Operational"
    p4.font.size = Pt(13)
    p4.font.color.rgb = RGBColor(148, 163, 184)

    # ==========================================
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2, BG_LIGHT)
    add_header(slide2, "The Retail Dilemma: Why Conventional Systems Fail", "EXECUTIVE SUMMARY & PROBLEM STATEMENT")

    # 3 Comparison Columns
    col_w = 3.65
    gap = 0.35
    start_x = 0.8
    top_y = 1.6
    card_h = 5.2

    # Column 1: The POS Disconnect
    add_card(slide2, start_x, top_y, col_w, card_h)
    tb = slide2.shapes.add_textbox(Inches(start_x + 0.25), Inches(top_y + 0.25), Inches(col_w - 0.5), Inches(card_h - 0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Point-of-Sale (POS) Blindspot"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ROSE

    items1 = [
        "Tracks checkout transactions accurately, but is physically blind to on-shelf reality.",
        "Cannot detect when front shelf rows are empty while stock sits forgotten in the backroom.",
        "Results in Phantom Inventory: the system thinks items exist, but customers find empty shelves.",
        "Lost sales, frustrated shoppers, and flawed reorder triggers."
    ]
    for it in items1:
        pi = tf.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(13)
        pi.font.color.rgb = TEXT_MAIN
        pi.space_before = Pt(10)

    # Column 2: The Camera/CV Flaw
    add_card(slide2, start_x + col_w + gap, top_y, col_w, card_h)
    tb = slide2.shapes.add_textbox(Inches(start_x + col_w + gap + 0.25), Inches(top_y + 0.25), Inches(col_w - 0.5), Inches(card_h - 0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Naive Computer Vision Limits"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    items2 = [
        "Standard cameras only perceive 2D front-facing surfaces without depth understanding.",
        "Suffers from False-Fronting: single products placed at the front conceal completely hollow shelves behind.",
        "High GPU inference costs if running continuous unoptimized video pipelines.",
        "Cannot verify backroom stock, wholesale costs, or lead times alone."
    ]
    for it in items2:
        pi = tf.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(13)
        pi.font.color.rgb = TEXT_MAIN
        pi.space_before = Pt(10)

    # Column 3: The RetailMind AI Solution
    add_card(slide2, start_x + (col_w + gap)*2, top_y, col_w, card_h, bg_color=RGBColor(240, 253, 244), border_color=PRIMARY)
    tb = slide2.shapes.add_textbox(Inches(start_x + (col_w + gap)*2 + 0.25), Inches(top_y + 0.25), Inches(col_w - 0.5), Inches(card_h - 0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Physical-Digital Fusion"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = PRIMARY

    items3 = [
        "Unites Computer Vision (YOLOv8 + CCTV) with real-time POS sales transactions.",
        "Accurately partitions inventory into Visible Shelf Stock vs. Estimated Backroom Reserve.",
        "Automatically identifies Shelf Restock, Phantom Stock, False-Fronting, and Shrinkage.",
        "Hybrid ML demand forecasting + automated dynamic reorder generation."
    ]
    for it in items3:
        pi = tf.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(13)
        pi.font.color.rgb = TEXT_MAIN
        pi.space_before = Pt(10)

    # ==========================================
    # SLIDE 3: SYSTEM ARCHITECTURE (6 TIERS)
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3, BG_LIGHT)
    add_header(slide3, "System Architecture: 6 Cohesive Operational Tiers", "TECHNICAL METHODOLOGY")

    tiers = [
        ("Tier 1: High-Throughput Async Backend", "FastAPI + SQLAlchemy 2.0 dual async/sync pooling + SQLite/PostgreSQL zero-config relational store.", PRIMARY),
        ("Tier 2: Computer Vision Shelf Detection", "Ultralytics YOLOv8 inference pipeline decoding incoming frames, regression bounding boxes & facing tallies.", ACCENT_INDIGO),
        ("Tier 3: Physical-Digital Fusion Engine", "Reconciles visible shelf counts (S_vis) with digital POS books (S_book) to compute backroom reserve and categorize discrepancies.", PRIMARY),
        ("Tier 4: ML Demand Forecasting & ROP", "60% EMA + 40% WMA hybrid time-series ensemble with dynamic confidence intervals and lead-time stockout risk alerts.", ACCENT_AMBER),
        ("Tier 5: CCTV Stream Video Ingestion", "OpenCV temporal frame sampler (1s-15s intervals), peak count aggregation, and keyframe audit timeline generation.", ACCENT_INDIGO),
        ("Tier 6: Store Owner Command Center", "React 19 + TypeScript + Vite + Tailwind CSS dashboard with Recharts live curves and single-click reconciliation.", PRIMARY)
    ]

    card_w = 5.7
    card_h = 1.6
    for i, (t_title, t_desc, accent_c) in enumerate(tiers):
        rx = 0.8 if i % 2 == 0 else 6.8
        ry = 1.6 + (i // 2) * 1.8
        add_card(slide3, rx, ry, card_w, card_h, border_color=accent_c)
        tb = slide3.shapes.add_textbox(Inches(rx + 0.2), Inches(ry + 0.15), Inches(card_w - 0.4), Inches(card_h - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = t_title
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = accent_c

        pd = tf.add_paragraph()
        pd.text = t_desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(4)

    # ==========================================
    # SLIDE 4: DATA ENGINEERING & SYNTHETIC DATASET
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4, BG_LIGHT)
    add_header(slide4, "Multi-Modal Dataset: Realistic Indian Retail Dynamics", "DATA ENGINEERING & PRE-PROCESSING")

    # 3 Stat Cards on Top
    stat_w = 3.65
    add_card(slide4, 0.8, 1.5, stat_w, 1.3, bg_color=RGBColor(240, 253, 244), border_color=PRIMARY)
    tb1 = slide4.shapes.add_textbox(Inches(0.95), Inches(1.6), Inches(stat_w - 0.3), Inches(1.1))
    tf1 = tb1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "15 Core Retail SKUs"
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = PRIMARY
    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Spanning 6 categories: Beverages, Snacks, Instant Foods, Biscuits, Dairy, Chocolates."
    p1_sub.font.size = Pt(11)
    p1_sub.font.color.rgb = TEXT_MUTED

    add_card(slide4, 0.8 + stat_w + 0.35, 1.5, stat_w, 1.3, bg_color=RGBColor(238, 242, 255), border_color=ACCENT_INDIGO)
    tb2 = slide4.shapes.add_textbox(Inches(0.8 + stat_w + 0.5), Inches(1.6), Inches(stat_w - 0.3), Inches(1.1))
    tf2 = tb2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = "12,391 POS Transactions"
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_INDIGO
    p2_sub = tf2.add_paragraph()
    p2_sub.text = "90 days of synthetic sales with realistic diurnal traffic curves and basket sizes."
    p2_sub.font.size = Pt(11)
    p2_sub.font.color.rgb = TEXT_MUTED

    add_card(slide4, 0.8 + (stat_w + 0.35)*2, 1.5, stat_w, 1.3, bg_color=RGBColor(254, 243, 199), border_color=ACCENT_AMBER)
    tb3 = slide4.shapes.add_textbox(Inches(0.8 + (stat_w + 0.35)*2 + 0.15), Inches(1.6), Inches(stat_w - 0.3), Inches(1.1))
    tf3 = tb3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = "25 FPS CCTV Video Stream"
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = ACCENT_AMBER
    p3_sub = tf3.add_paragraph()
    p3_sub.text = "Multi-camera perspective overhead footage with temporal frame extraction."
    p3_sub.font.size = Pt(11)
    p3_sub.font.color.rgb = TEXT_MUTED

    # Bottom Detailed Split (Catalog + Transaction Dynamics)
    b_left = add_card(slide4, 0.8, 3.1, 5.7, 3.7)
    tb_bl = slide4.shapes.add_textbox(Inches(1.0), Inches(3.3), Inches(5.3), Inches(3.3))
    tf_bl = tb_bl.text_frame
    tf_bl.word_wrap = True
    p_bl = tf_bl.paragraphs[0]
    p_bl.text = "SKU Catalog Parameters"
    p_bl.font.size = Pt(16)
    p_bl.font.bold = True
    p_bl.font.color.rgb = BG_DARK

    sku_points = [
        "Pricing & Margins: Retail Price (P) and Wholesale Cost (C) mapped for gross margin tracking.",
        "Supplier Lead Times: Stochastic lead times L in [1, 4] days for realistic reorder scheduling.",
        "Safety Stock & Shelf Caps: Min safety stock S_safe in [8, 30] units; Planogram shelf capacity C_shelf in [16, 48].",
        "Planogram Zones: Associated with camera IDs, shelf levels, and bounding polygon coordinates."
    ]
    for sp in sku_points:
        p_item = tf_bl.add_paragraph()
        p_item.text = "• " + sp
        p_item.font.size = Pt(12)
        p_item.font.color.rgb = TEXT_MAIN
        p_item.space_before = Pt(8)

    b_right = add_card(slide4, 6.8, 3.1, 5.7, 3.7)
    tb_br = slide4.shapes.add_textbox(Inches(7.0), Inches(3.3), Inches(5.3), Inches(3.3))
    tf_br = tb_br.text_frame
    tf_br.word_wrap = True
    p_br = tf_br.paragraphs[0]
    p_br.text = "Realistic Transaction Stochasticity"
    p_br.font.size = Pt(16)
    p_br.font.bold = True
    p_br.font.color.rgb = BG_DARK

    pos_points = [
        "Diurnal Curves: Bi-modal shopper traffic peaking at lunch (11 AM - 2 PM) and evening (6 PM - 9:30 PM).",
        "Weekend Multipliers: 1.35x - 1.65x surge in retail transaction volume on Fri, Sat, Sun.",
        "Basket Distribution: Realistic multi-item shopping baskets with variable quantity multipliers.",
        "Payment Methods: Emulates Indian retail reality (62% UPI, 23% Credit/Debit Card, 15% Cash)."
    ]
    for pp in pos_points:
        p_item = tf_br.add_paragraph()
        p_item.text = "• " + pp
        p_item.font.size = Pt(12)
        p_item.font.color.rgb = TEXT_MAIN
        p_item.space_before = Pt(8)

    # ==========================================
    # SLIDE 5: COMPUTER VISION & CCTV STREAM PIPELINE
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5, BG_LIGHT)
    add_header(slide5, "Computer Vision & CCTV Video Pipeline", "OBJECT DETECTION & CONTINUOUS SURVEILLANCE")

    # Left: Steps
    add_card(slide5, 0.8, 1.5, 6.5, 5.3)
    tb_cv = slide5.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(6.1), Inches(4.9))
    tf_cv = tb_cv.text_frame
    tf_cv.word_wrap = True
    p_cv = tf_cv.paragraphs[0]
    p_cv.text = "YOLOv8 & OpenCV Ingestion Workflow"
    p_cv.font.size = Pt(18)
    p_cv.font.bold = True
    p_cv.font.color.rgb = BG_DARK

    cv_steps = [
        ("1. Image Byte Ingestion & Preprocessing", "Decodes uploaded JPEG/PNG or video frame buffers into standard BGR NumPy arrays without disk write locks."),
        ("2. Bounding Box & Class Regression", "Ultralytics YOLOv8 architecture executes fast object inference with non-maximum suppression (NMS) and confidence filtering."),
        ("3. Visible Product Aggregation (S_vis)", "Calculates total visible front-facing units grouped by SKU class across shelf planograms."),
        ("4. CCTV Video Temporal Sampling", "Extracts keyframes at configurable delta t (1s-15s), bypassing 25 FPS GPU bottlenecks while tracking aisle traffic."),
        ("5. Peak Facings & Visual Audit Log", "Retains maximum observed front-facing items across the observation window and saves keyframe snapshots for visual auditing.")
    ]
    for st_title, st_desc in cv_steps:
        p_st = tf_cv.add_paragraph()
        p_st.text = st_title
        p_st.font.size = Pt(13)
        p_st.font.bold = True
        p_st.font.color.rgb = PRIMARY
        p_st.space_before = Pt(10)

        p_desc = tf_cv.add_paragraph()
        p_desc.text = st_desc
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = TEXT_MAIN

    # Right: Performance Callout Card
    add_card(slide5, 7.6, 1.5, 4.9, 5.3, bg_color=RGBColor(241, 245, 249), border_color=CARD_BORDER)
    tb_perf = slide5.shapes.add_textbox(Inches(7.85), Inches(1.7), Inches(4.4), Inches(4.9))
    tf_perf = tb_perf.text_frame
    tf_perf.word_wrap = True
    p_perf = tf_perf.paragraphs[0]
    p_perf.text = "Vision Latency & Throughput"
    p_perf.font.size = Pt(18)
    p_perf.font.bold = True
    p_perf.font.color.rgb = ACCENT_INDIGO

    perf_stats = [
        ("18.4 ms", "Average GPU Inference Latency (YOLOv8n)"),
        ("210 - 280 ms", "Average CPU Inference Latency (Standard Hardware)"),
        ("< 1.8 seconds", "8-Second 25 FPS Video Sampling (200 frames @ 3s intervals)"),
        ("Zero Overhead", "Runs smoothly on commodity PCs without requiring cloud GPU clusters")
    ]
    for num, lbl in perf_stats:
        p_num = tf_perf.add_paragraph()
        p_num.text = num
        p_num.font.size = Pt(22)
        p_num.font.bold = True
        p_num.font.color.rgb = BG_DARK
        p_num.space_before = Pt(12)

        p_lbl = tf_perf.add_paragraph()
        p_lbl.text = lbl
        p_lbl.font.size = Pt(11)
        p_lbl.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 6: PHYSICAL-DIGITAL FUSION & DISCREPANCY CLASSIFICATION
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6, BG_LIGHT)
    add_header(slide6, "Physical-Digital Fusion: 4 Automated Discrepancy Classes", "INVENTORY RECONCILIATION ENGINE")

    # Math Card
    add_card(slide6, 0.8, 1.5, 11.7, 1.1, bg_color=RGBColor(240, 253, 244), border_color=PRIMARY)
    tb_math = slide6.shapes.add_textbox(Inches(1.0), Inches(1.55), Inches(11.3), Inches(1.0))
    tf_math = tb_math.text_frame
    p_m1 = tf_math.paragraphs[0]
    p_m1.text = "Core Fusion Formulation: Partitioning Inventory"
    p_m1.font.size = Pt(14)
    p_m1.font.bold = True
    p_m1.font.color.rgb = PRIMARY
    p_m2 = tf_math.add_paragraph()
    p_m2.text = "• S_book = S_initial + Deliveries - POS Sales - Adjustments   |   • S_vis = YOLO Visible Facings   |   • Estimated Backroom = max(0, S_book - S_vis)"
    p_m2.font.size = Pt(12)
    p_m2.font.color.rgb = BG_DARK

    # 4 Discrepancy Types (2x2 Grid)
    discrepancies = [
        ("1. Shelf Restock Needed", "S_vis <= Threshold, but S_back >= 3 units", "Front shelf display is starving while stock exists in backroom storage. Prompts store floor staff to restock immediately.", ACCENT_AMBER),
        ("2. Phantom Stock (Ghost Inventory)", "S_book > 0, but Physical Audit = 0", "Digital ledger says product exists, but physical shelves and backroom are empty. Freezes automated reordering until reconciled.", ACCENT_ROSE),
        ("3. Inventory Shrinkage & Loss", "Audited Physical Total < S_book", "Physical stock is less than ledger. System calculates exact financial loss: Loss = |S_phys - S_book| * Price and creates audit log.", ACCENT_INDIGO),
        ("4. False-Fronting Detection", "S_vis > 0, but S_book <= S_vis on Deep Shelves", "Single row of products at the front masks a hollow shelf behind. Uncovers misleading planograms before customers face empty depth.", PRIMARY)
    ]

    for i, (d_title, d_cond, d_expl, d_col) in enumerate(discrepancies):
        dx = 0.8 if i % 2 == 0 else 6.8
        dy = 2.8 + (i // 2) * 2.0
        add_card(slide6, dx, dy, 5.7, 1.85, border_color=d_col)
        tb_d = slide6.shapes.add_textbox(Inches(dx + 0.2), Inches(dy + 0.15), Inches(5.3), Inches(1.55))
        tf_d = tb_d.text_frame
        tf_d.word_wrap = True

        pt = tf_d.paragraphs[0]
        pt.text = d_title
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = d_col

        pc = tf_d.add_paragraph()
        pc.text = "Trigger: " + d_cond
        pc.font.size = Pt(11)
        pc.font.bold = True
        pc.font.color.rgb = BG_DARK
        pc.space_before = Pt(2)

        pe = tf_d.add_paragraph()
        pe.text = d_expl
        pe.font.size = Pt(11)
        pe.font.color.rgb = TEXT_MUTED
        pe.space_before = Pt(3)

    # ==========================================
    # SLIDE 7: DEMAND FORECASTING & DYNAMIC REORDER POINT
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7, BG_LIGHT)
    add_header(slide7, "ML Demand Forecasting & Dynamic Reorder Point", "PREDICTIVE ANALYTICS & REPLENISHMENT")

    # Left: Forecasting Ensemble
    add_card(slide7, 0.8, 1.5, 5.7, 5.3)
    tb_fc = slide7.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.9))
    tf_fc = tb_fc.text_frame
    tf_fc.word_wrap = True
    p_fc = tf_fc.paragraphs[0]
    p_fc.text = "Hybrid Time-Series Ensemble"
    p_fc.font.size = Pt(18)
    p_fc.font.bold = True
    p_fc.font.color.rgb = BG_DARK

    fc_details = [
        ("60% Exponential Moving Average (EMA)", "alpha = 0.3 captures recent demand momentum, promotional sales spikes, and immediate shifts in consumer velocity."),
        ("40% Weighted Moving Average (WMA)", "Linear recency weights across 7-day to 30-day windows smooth out short-term random noise and stochastic outliers."),
        ("Dynamic Confidence Intervals", "Confidence = max(0.40, 0.95 - 0.30 * CV) where CV = sigma / mu. High-variance SKUs dynamically receive wider prediction bands."),
        ("14-Day Forward Horizon", "Generates daily expected sales with lower/upper bounds for proactive procurement planning.")
    ]
    for h_txt, b_txt in fc_details:
        ph = tf_fc.add_paragraph()
        ph.text = "• " + h_txt
        ph.font.size = Pt(13)
        ph.font.bold = True
        ph.font.color.rgb = PRIMARY
        ph.space_before = Pt(8)

        pb = tf_fc.add_paragraph()
        pb.text = b_txt
        pb.font.size = Pt(11)
        pb.font.color.rgb = TEXT_MAIN

    # Right: Reorder Point Optimization
    add_card(slide7, 6.8, 1.5, 5.7, 5.3)
    tb_rop = slide7.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.9))
    tf_rop = tb_rop.text_frame
    tf_rop.word_wrap = True
    p_rop = tf_rop.paragraphs[0]
    p_rop.text = "Dynamic Reorder Point (ROP)"
    p_rop.font.size = Pt(18)
    p_rop.font.bold = True
    p_rop.font.color.rgb = BG_DARK

    rop_details = [
        ("Mathematical Formulation", "ROP = (Daily Run Rate * Supplier Lead Time) + Safety Stock"),
        ("Stockout Risk Stratification", "• CRITICAL: Days until depletion <= Lead Time L\n• HIGH: Days until depletion <= 2 * L\n• MEDIUM: S_book <= ROP\n• LOW / NONE: Healthy inventory buffer"),
        ("Automated Purchase Orders", "Computes Suggested Order Quantity to restore inventory to full shelf capacity plus safety buffer."),
        ("Workflow Lifecycle", "One-click approval workflow in dashboard (Approve -> Order Placed -> Received & Reconciled).")
    ]
    for h_txt, b_txt in rop_details:
        ph = tf_rop.add_paragraph()
        ph.text = "• " + h_txt
        ph.font.size = Pt(13)
        ph.font.bold = True
        ph.font.color.rgb = ACCENT_AMBER
        ph.space_before = Pt(8)

        pb = tf_rop.add_paragraph()
        pb.text = b_txt
        pb.font.size = Pt(11)
        pb.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 8: STORE OWNER COMMAND CENTER (FRONTEND)
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8, BG_LIGHT)
    add_header(slide8, "Store Owner Command Center: Interactive Web UI", "FRONTEND IMPLEMENTATION (REACT 19 + TAILWIND)")

    ui_tabs = [
        ("1. Executive Overview", "Live inventory value, overall shelf fill gauge, critical alert count, and 90-day store revenue trajectory."),
        ("2. Real-Time Inventory Matrix", "15-SKU ledger displaying visible vs book stock, backroom estimates, and instant physical audit adjustment modals."),
        ("3. AI Vision & CCTV Scanner", "Drag-and-drop shelf photo analyzer, continuous CCTV video player, peak facings metrics, and keyframe audit timeline."),
        ("4. Demand Forecasting Hub", "14-day interactive forecast curves with shaded confidence bands, run rates, and one-click purchase order triggers."),
        ("5. POS Analytics & Insights", "30-day velocity curves, basket size distribution, payment breakdown (UPI/Card/Cash), and granular receipt ledger."),
        ("6. Alert Triage Stream", "Color-coded priority queue for stockouts, low inventory, and shrinkage with single-click resolution actions.")
    ]

    for i, (tab_title, tab_desc) in enumerate(ui_tabs):
        tx = 0.8 if i % 2 == 0 else 6.8
        ty = 1.6 + (i // 2) * 1.8
        add_card(slide8, tx, ty, 5.7, 1.6)
        tb_ui = slide8.shapes.add_textbox(Inches(tx + 0.2), Inches(ty + 0.15), Inches(5.3), Inches(1.3))
        tf_ui = tb_ui.text_frame
        tf_ui.word_wrap = True
        pt = tf_ui.paragraphs[0]
        pt.text = tab_title
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY

        pd = tf_ui.add_paragraph()
        pd.text = tab_desc
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(4)

    # ==========================================
    # SLIDE 9: EXPERIMENTAL RESULTS & VERIFICATION
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9, BG_LIGHT)
    add_header(slide9, "Experimental Results & Full Verification Matrix", "SYSTEM EVALUATION & TESTING")

    # Big 100% Metric Card on Left
    add_card(slide9, 0.8, 1.5, 3.8, 5.3, bg_color=RGBColor(240, 253, 244), border_color=PRIMARY)
    tb_m = slide9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.4), Inches(4.7))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    pm = tf_m.paragraphs[0]
    pm.text = "74 / 74"
    pm.font.size = Pt(44)
    pm.font.bold = True
    pm.font.color.rgb = PRIMARY

    pm2 = tf_m.add_paragraph()
    pm2.text = "TESTS PASSED (100%)"
    pm2.font.size = Pt(14)
    pm2.font.bold = True
    pm2.font.color.rgb = BG_DARK

    pm3 = tf_m.add_paragraph()
    pm3.text = "\n• 9 Complete Test Modules\n• Full Backend & Lifespan\n• YOLOv8 Bounding Validation\n• Fusion Engine Reconciliation\n• Demand Ensemble Logic\n• CCTV Video Sampling\n• Stock Adjustment Integrity"
    pm3.font.size = Pt(12)
    pm3.font.color.rgb = TEXT_MAIN

    # Right: Test Suite Summary Table
    add_card(slide9, 4.9, 1.5, 7.6, 5.3)
    tb_tbl = slide9.shapes.add_textbox(Inches(5.1), Inches(1.7), Inches(7.2), Inches(4.9))
    tf_tbl = tb_tbl.text_frame
    tf_tbl.word_wrap = True
    ptbl = tf_tbl.paragraphs[0]
    ptbl.text = "Automated Test Suite Breakdown"
    ptbl.font.size = Pt(18)
    ptbl.font.bold = True
    ptbl.font.color.rgb = BG_DARK

    test_rows = [
        ("test_health.py", "Database connectivity & FastAPI lifespan startup", "PASSED (2/2)"),
        ("test_seed_data.py", "15 SKUs integrity, 90-day POS generation, price constraints", "PASSED (3/3)"),
        ("test_products.py", "Catalog filters, SKU lookup, planogram zone mappings", "PASSED (4/4)"),
        ("test_sales.py", "Transaction ledger pagination, revenue & daily aggregates", "PASSED (4/4)"),
        ("test_alerts.py", "Alert queue dispatch, priority triage, resolution lifecycle", "PASSED (3/3)"),
        ("test_vision.py", "YOLO inference, bounding boxes, MIME checks, static files", "PASSED (5/5)"),
        ("test_inventory_fusion.py", "Discrepancy engine, shrinkage, phantom stock detection", "PASSED (8/8)"),
        ("test_forecast.py", "EMA/WMA ensemble, confidence bounds, ROP PATCH routes", "PASSED (40/40)"),
        ("test_cctv.py", "Video upload, frame sampling, peak facings extraction", "PASSED (5/5)")
    ]
    for fname, scope, res in test_rows:
        pr = tf_tbl.add_paragraph()
        pr.text = f"• {fname}: {scope} — {res}"
        pr.font.size = Pt(11)
        pr.font.color.rgb = TEXT_MAIN
        pr.space_before = Pt(4)

    # ==========================================
    # SLIDE 10: BUSINESS VALUE & REAL-WORLD IMPACT
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10, BG_LIGHT)
    add_header(slide10, "Business Value & Real-World ROI", "OPERATIONAL IMPACT")

    # 4 ROI Pillars
    roi_cards = [
        ("70 - 85% Stockout Reduction", "Eliminates empty shelves while backroom stock is available. Staff receive targeted alerts before customers face out-of-stock items.", PRIMARY),
        ("90% Faster Physical Audits", "Automates visual shelf audits through CCTV/cameras, replacing tedious manual barcode scans with one-click reconciliation.", ACCENT_INDIGO),
        ("Shrinkage & Theft Visibility", "Exposes the exact dollar cost of lost/stolen inventory by comparing physical counts with expected ledger totals.", ACCENT_ROSE),
        ("Optimized Working Capital", "Prevents overstocking on slow-moving goods and avoids supplier stockouts by computing dynamic safety stocks and lead times.", ACCENT_AMBER)
    ]

    for i, (rtitle, rdesc, rcol) in enumerate(roi_cards):
        cx = 0.8 if i % 2 == 0 else 6.8
        cy = 1.6 + (i // 2) * 2.6
        add_card(slide10, cx, cy, 5.7, 2.3, border_color=rcol)
        tb_roi = slide10.shapes.add_textbox(Inches(cx + 0.3), Inches(cy + 0.2), Inches(5.1), Inches(1.9))
        tf_roi = tb_roi.text_frame
        tf_roi.word_wrap = True

        pt = tf_roi.paragraphs[0]
        pt.text = rtitle
        pt.font.size = Pt(18)
        pt.font.bold = True
        pt.font.color.rgb = rcol

        pd = tf_roi.add_paragraph()
        pd.text = rdesc
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(8)

    # ==========================================
    # SLIDE 11: CONCLUSION & FUTURE ROADMAP
    # ==========================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11, BG_LIGHT)
    add_header(slide11, "Conclusion & Future Roadmap", "PROJECT SUMMARY & NEXT HORIZONS")

    # Left: Summary
    add_card(slide11, 0.8, 1.5, 5.7, 5.3)
    tb_c = slide11.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.9))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    pc_t = tf_c.paragraphs[0]
    pc_t.text = "Key Project Takeaways"
    pc_t.font.size = Pt(18)
    pc_t.font.bold = True
    pc_t.font.color.rgb = BG_DARK

    takeaways = [
        "RetailMind AI bridges the historical divide between digital POS accounting and physical shelf reality.",
        "Computer Vision + Sales Ledger Fusion provides complete visibility into shelf availability, phantom stock, and shrinkage.",
        "Delivered as an end-to-end, production-ready full-stack system with 74/74 passing automated tests.",
        "Proven to operate efficiently on commodity retail hardware without requiring expensive GPU clusters or proprietary RFID tags."
    ]
    for tk in takeaways:
        ptk = tf_c.add_paragraph()
        ptk.text = "• " + tk
        ptk.font.size = Pt(13)
        ptk.font.color.rgb = TEXT_MAIN
        ptk.space_before = Pt(12)

    # Right: Roadmap
    add_card(slide11, 6.8, 1.5, 5.7, 5.3)
    tb_rd = slide11.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.9))
    tf_rd = tb_rd.text_frame
    tf_rd.word_wrap = True
    prd_t = tf_rd.paragraphs[0]
    prd_t.text = "Future Technical Scope"
    prd_t.font.size = Pt(18)
    prd_t.font.bold = True
    prd_t.font.color.rgb = PRIMARY

    roadmap = [
        ("1. Edge AI Deployment", "Quantizing YOLO models (ONNX / TensorRT / INT8) for low-power edge gateways (Raspberry Pi 5 / NVIDIA Jetson Orin Nano)."),
        ("2. Planogram Heatmaps & Dwell Time", "Generating visual customer aisle engagement heatmaps and traffic dwell-time analytics from overhead CCTV streams."),
        ("3. Wholesaler ERP & EDI Integration", "Direct integration with Tally, SAP, and Zoho Inventory for automated, touchless purchase order dispatch."),
        ("4. Active RF / BLE Beacon Tagging", "Hybridizing vision with low-cost BLE beacons for automated backroom asset localization.")
    ]
    for rh, rb in roadmap:
        prh = tf_rd.add_paragraph()
        prh.text = rh
        prh.font.size = Pt(13)
        prh.font.bold = True
        prh.font.color.rgb = PRIMARY
        prh.space_before = Pt(8)

        prb = tf_rd.add_paragraph()
        prb.text = rb
        prb.font.size = Pt(11)
        prb.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 12: THANK YOU & Q&A (Dark Theme)
    # ==========================================
    slide12 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide12, BG_DARK)

    tb_end = slide12.shapes.add_textbox(Inches(1.5), Inches(2.0), Inches(10.3), Inches(3.5))
    tf_end = tb_end.text_frame
    tf_end.word_wrap = True

    pe1 = tf_end.paragraphs[0]
    pe1.alignment = PP_ALIGN.CENTER
    pe1.text = "Thank You!"
    pe1.font.size = Pt(48)
    pe1.font.bold = True
    pe1.font.color.rgb = PRIMARY_LIGHT

    pe2 = tf_end.add_paragraph()
    pe2.alignment = PP_ALIGN.CENTER
    pe2.text = "RetailMind AI: Smart Retail Inventory & Store Intelligence"
    pe2.font.size = Pt(22)
    pe2.font.color.rgb = TEXT_LIGHT
    pe2.space_before = Pt(10)

    pe3 = tf_end.add_paragraph()
    pe3.alignment = PP_ALIGN.CENTER
    pe3.text = "\nHarshit Pahuja (S24CSEU0736)  |  Manan Jain (S24CSEU0219)\nDepartment of Computer Science & Engineering"
    pe3.font.size = Pt(15)
    pe3.font.color.rgb = RGBColor(148, 163, 184)
    pe3.space_before = Pt(10)

    pe4 = tf_end.add_paragraph()
    pe4.alignment = PP_ALIGN.CENTER
    pe4.text = "\nQuestions & Discussion"
    pe4.font.size = Pt(20)
    pe4.font.bold = True
    pe4.font.color.rgb = ACCENT_AMBER
    pe4.space_before = Pt(14)

    output_path = r"C:\Users\Harshit Pahuja\Desktop\RetailMindAI\RetailMind_AI_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_deck()
