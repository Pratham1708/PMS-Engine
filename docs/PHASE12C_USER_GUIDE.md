# PMS Engine Phase 12C — User Guide

Welcome to the PMS Engine Institutional Research Reports module. This guide explains how to generate, preview, and export research reports.

---

## 1. Stock Research Report Flow

The equity research reporting workflow is integrated directly into individual stock pages to behave like a Bloomberg or Morningstar terminal.

### Step-by-Step Flow:
1. **Search & Navigate**: Locate any Nifty 50 stock in the **Stock Search** tab (e.g. `RELIANCE.NS`).
2. **Execute Engine**: Click the **🔬 RUN PMS ANALYSIS** button. This will start the progressive analysis, revealing indicators sequentially.
3. **Generate Report**: Once the progressive reveal finishes and Section 9 (Explainable AI justifications) is loaded, a green card labeled **📄 Equity Research Report Available** will render.
4. **Compile**: Click **📄 GENERATE RESEARCH REPORT**. The backend will compile the live quote, technical data, and model scores into professional layouts.
5. **Preview & Download**: An interactive **Report Preview** frame will mount inside the stock page. Use the top action buttons to download in PDF (**📥 Download PDF**) or HTML (**🌐 Download HTML**) format.

---

## 2. Research Workspace Report

The workspace report represents a deep-dive analysis of your tracked stocks and history coverage. It replaces the old portfolio reports concept.

### Step-by-Step Flow:
1. **Add to Workspace**: Navigate to any stock and click **＋ Track in Workspace**.
2. **Open Reports Page**: Go to **Research Reports** in the left sidebar.
3. **Workspace Card**: Locate the **💼 Research Workspace Report** card.
4. **Actions**:
   - Click **📄 Generate Workspace Report** to compile and preview the workspace report inline.
   - Or click **📥 PDF** / **🌐 HTML** in the **Direct Export** block to export and download the file immediately.

The workspace report highlights:
- Total tracked stocks count vs the total universe (coverage ratio).
- Most Bullish (highest composite score), Most Bearish (lowest composite score), and Highest Conviction (highest confidence) stocks.
- Detailed tables listing all tracked stocks and recent analysis history logs.

---

## 3. Market Overview Report

The market overview report provides a broad-scale statistical analysis of the Nifty 50 scanner universe.

### Step-by-Step Flow:
1. **Navigate**: Open the **Research Reports** page.
2. **Market Card**: Locate the **🌐 Market Overview Report** card.
3. **Actions**:
   - Click **📄 Generate Market Report** to preview the layout inside the iframe.
   - Use the **Direct Export** links to download the files instantly.

The market report compiles:
- Universe averages (Average Technical Score, Average ML Score, Average GRU Score, Average Confidence).
- Rating counts and percentages distribution (Strong Buy, Buy, Hold, Sell, Strong Sell).
- Market breadth summary and decile rankings.

---

## 4. Historical Archive & Download Center

At the bottom of the **Research Reports** page, the **📋 Report History** card logs every report generated on the platform:
- The history lists report type, UUID ID, stock symbol (for stock reports), and generation timestamp.
- Click the eye icon (**👁️**) to preview any archived report instantly.
- Click the download icons to fetch the files directly.
- **Freshness Cache**: If you request a report for a stock that has not changed its analysis state, or a market report generated in the last hour, the system will reuse the pre-compiled file immediately, skipping render times.
