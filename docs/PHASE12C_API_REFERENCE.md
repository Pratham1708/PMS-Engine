# PMS Engine Phase 12C — API Reference

This document describes all API endpoints exposed under the `/api/reports` module in the PMS Engine backend.

---

## 1. Stock Research Reports

### 1.1 Generate/Get Stock Report Metadata
* **Endpoint**: `GET /api/reports/stock/{symbol}`
* **Description**: Compiles live data, ML/GRU scores, rating conviction, and XAI justifications. Generates/saves the report files and returns report metadata.
* **Parameters**:
  - `symbol` (string, path): Stock ticker symbol (e.g. `RELIANCE.NS`).
* **Response (HTTP 200)**:
  ```json
  {
    "report_id": "fa4a6165-6620-47bf-8178-96b5ce0c002d",
    "type": "stock",
    "symbol": "RELIANCE.NS",
    "html_path": "C:\\path\\to\\backend\\data\\reports\\stock\\fa4a6165-6620-47bf-8178-96b5ce0c002d.html",
    "pdf_path": "C:\\path\\to\\backend\\data\\reports\\stock\\fa4a6165-6620-47bf-8178-96b5ce0c002d.pdf",
    "generated_at": "2026-06-11T16:46:30.811896",
    "analysis_id": "634af083-a471-4ecb-b0e5-65edd4bb6225"
  }
  ```

### 1.2 Export Stock Report PDF
* **Endpoint**: `GET /api/reports/stock/{symbol}/pdf`
* **Description**: Generates (or pulls fresh cache) and directly streams the PDF file.
* **Media Type**: `application/pdf`
* **Header**: `content-disposition: attachment; filename="Research_Report_{SYMBOL}.pdf"`

### 1.3 Export Stock Report HTML
* **Endpoint**: `GET /api/reports/stock/{symbol}/html`
* **Description**: Generates (or pulls fresh cache) and directly streams the HTML file.
* **Media Type**: `text/html`
* **Header**: `content-disposition: attachment; filename="Research_Report_{SYMBOL}.html"`

---

## 2. Research Workspace Reports

### 2.1 Generate/Get Workspace Report Metadata
* **Endpoint**: `GET /api/reports/workspace`
* **Description**: Compiles user interest stocks coverage, total universe stats, highlight markers, and automated workspace insights.
* **Response (HTTP 200)**:
  ```json
  {
    "report_id": "7e92a79d-d8af-43fb-89cf-0fdee3c617c3",
    "type": "workspace",
    "symbol": null,
    "html_path": "C:\\path\\to\\backend\\data\\reports\\workspace\\7e92a79d-d8af-43fb-89cf-0fdee3c617c3.html",
    "pdf_path": "C:\\path\\to\\backend\\data\\reports\\workspace\\7e92a79d-d8af-43fb-89cf-0fdee3c617c3.pdf",
    "generated_at": "2026-06-11T16:47:40.294464",
    "analysis_id": null
  }
  ```

### 2.2 Export Workspace PDF
* **Endpoint**: `GET /api/reports/workspace/pdf`
* **Description**: Direct file stream download of workspace PDF.
* **Media Type**: `application/pdf`

### 2.3 Export Workspace HTML
* **Endpoint**: `GET /api/reports/workspace/html`
* **Description**: Direct file stream download of workspace HTML.
* **Media Type**: `text/html`

---

## 3. Market Research Reports

### 3.1 Generate/Get Market Report Metadata
* **Endpoint**: `GET /api/reports/market`
* **Description**: Compiles Nifty 50 universe scoring, ratings counts distribution, and top/bottom decile holdings lists.
* **Response (HTTP 200)**:
  ```json
  {
    "report_id": "bde50e5f-1a44-4b44-868a-6d609f082326",
    "type": "market",
    "symbol": null,
    "html_path": "C:\\path\\to\\backend\\data\\reports\\market\\bde50e5f-1a44-4b44-868a-6d609f082326.html",
    "pdf_path": "C:\\path\\to\\backend\\data\\reports\\market\\bde50e5f-1a44-4b44-868a-6d609f082326.pdf",
    "generated_at": "2026-06-11T16:47:39.386287",
    "analysis_id": null
  }
  ```

### 3.2 Export Market PDF
* **Endpoint**: `GET /api/reports/market/pdf`
* **Description**: Direct file stream download of market PDF.
* **Media Type**: `application/pdf`

### 3.3 Export Market HTML
* **Endpoint**: `GET /api/reports/market/html`
* **Description**: Direct file stream download of market HTML.
* **Media Type**: `text/html`

---

## 4. History Listing & Utility Views

### 4.1 List Report History
* **Endpoint**: `GET /api/reports/list`
* **Description**: Returns all generated reports listed in the SQLite history database.
* **Response (HTTP 200)**:
  ```json
  [
    {
      "report_id": "7e92a79d-d8af-43fb-89cf-0fdee3c617c3",
      "type": "workspace",
      "symbol": null,
      "generated_at": "2026-06-11T16:47:40.294464",
      "analysis_id": null,
      "has_pdf": true
    }
  ]
  ```

### 4.2 Preview Report HTML (Iframe Viewer)
* **Endpoint**: `GET /api/reports/preview/{report_id}`
* **Description**: Serves the raw HTML report directly as a web page, suitable for mounting inside an iframe.
* **Media Type**: `text/html`

### 4.3 Download Report by ID
* **Endpoint**: `GET /api/reports/download/{report_id}?format={pdf|html}`
* **Description**: Downloads a historically generated report file by its report ID and format.
* **Parameters**:
  - `format` (string, query): Options are `pdf` or `html`. Default is `pdf`.
