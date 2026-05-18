# ComplyOS: Natural Language Rule Engine for XML Invoice Validation
## Complete Project Report & Documentation

---

### 1. Project Overview & Problem Statement
**ComplyOS** is a complete, startup-grade web platform designed to solve the complexity of tax-compliant e-invoicing. Currently, invoice validation systems rely on hardcoded XSLT scripts and developer-only configurations. 

**ComplyOS** provides a deterministic environment where non-technical users can define invoice validation rules in plain English. The engine parses the rules, generates an Intermediate Representation (IR), builds executable XSLT mappings, and processes physical XML invoices to return an **Explainable Trace Log**.

---

### 2. End-to-End Workflow (How it Works)

The platform follows a strict, deterministic 4-step pipeline:

1. **Natural Language Input (Rule Studio & Templates)**
   - The user visits the **Rule Studio** (or selects a pre-built rule from **Rule Templates**).
   - They type a rule in plain English: *"If tax amount > 0 tax category is required"*.
   
2. **Deterministic Parsing & IR Generation (Backend)**
   - The React frontend sends the text to the FastAPI backend.
   - Using **Semantic Regex Mapping** (avoiding unpredictable LLM hallucinations), the backend parses the text into a structured JSON object called the **Intermediate Representation (IR)**.
   - Automatically, an enterprise-grade `XSLT` script is generated from the IR.
   
3. **Dynamic Rule Binding (React Context)**
   - Once a rule is parsed, it is globally saved into the `RuleContext` state management system.
   - The user navigates to the **XML Validator** page, where their newly created rule is automatically selected in the "Active Rule" dropdown.

4. **XML Execution & Explainable Traces (Validator)**
   - The user drags and drops a physical `.xml` invoice.
   - The backend runs the exact active rule against the XML nodes using namespace-agnostic resolution (generalization).
   - The UI outputs an **Explainable Trace Log** indicating a **PASS** or **FAIL**, with exact details (e.g., *"Condition met, tax_category is present."* or *"Field missing."*).

---

### 3. Detailed Features & Pages

#### **Home Page (`/`)**
- **Purpose**: A premium landing page introducing the platform.
- **Features**: Animated hero sections, a visual mapping of the 4-step execution flow, and "How it Works" cards.

#### **Onboarding Modal (`Onboarding.jsx`)**
- **Purpose**: Guides first-time users.
- **Features**: A high-fidelity "spotlight" tutorial that triggers on the first visit. It walks the user sequentially through the core pages using `localStorage` caching.

#### **Dashboard (`/dashboard`)**
- **Purpose**: Top-level analytics and health monitoring.
- **Features**: 
  - Real-time KPI Stat Cards (Active Rules, Processed Invoices, Validation Errors, System Uptime).
  - A responsive Recharts Donut chart showing Pass vs. Fail ratios.
  - A live activity feed showing recent validation traces.

#### **Rule Studio (`/studio`)**
- **Purpose**: The core engine input interface.
- **Features**: 
  - Natural Language Textarea.
  - **IR Preview Panel**: Real-time rendering of the JSON syntax tree.
  - **XSLT Output Panel**: Displays the exact generated `<xsl:stylesheet>`.

#### **Rule Templates (`/templates`)**
- **Purpose**: Quick-start library for non-technical users.
- **Features**: Contains 9+ pre-configured logic templates covering all Problem Statement requirements (Required Fields, Date Rules, Numeric Comparisons, Currency Consistency, etc.). Clicking "Use Template" instantly routes the rule back to the Studio.

#### **XML Validator (`/validator`)**
- **Purpose**: The execution playground.
- **Features**:
  - Drag-and-drop animated file upload zone.
  - **Active Rule Dropdown**: Select which rule to run the XML against.
  - **Explainable Output**: Prints critical hard errors and a dynamic trace log explaining exactly why a rule passed or failed.

#### **Analytics (`/analytics`)**
- **Purpose**: Deep-dive validation metrics.
- **Features**:
  - **Failure Density Matrix**: A custom-built Heatmap grid mapping Rule Categories against days of the week.
  - **Execution Bar & Area Charts**: Breakdown of rule execution popularity and historical volume.

#### **Settings (`/settings`)**
- **Purpose**: Global preferences.
- **Features**: Toggles for Dark Mode, Validation Severity Defaults, and caching controls.

---

### 4. Extra Features (Beyond the Problem Statement)

To ensure this project was "Startup-Grade" and visually spectacular, the following features were engineered beyond the basic requirements:

1. **Native Adaptive Dark Mode**: Implemented a flawless Dark Mode utilizing semantic CSS variables (`--color-surface`, `--color-background`) and responsive `color-mix()` transparent borders. The entire platform natively shifts from Premium Cream (`#fafaf9`) to Deep Navy (`#0f172a`) seamlessly.
2. **Glassmorphism UI Framework**: Custom CSS utility classes (`.glass-panel`) provide iOS-style background blurring and soft shadows.
3. **Dynamic Rule Context Binding**: Implemented a global React `RuleContext` pipeline. Rules parsed in the Studio automatically migrate to the Validator dropdown without needing manual copy-pasting or database lookups.
4. **Custom Failure Density Heatmap**: Built a complex, mathematical Heatmap component in the Analytics tab from scratch, utilizing dynamic intensity classes.
5. **Mass Synthetic Data Generator (`backend/datasets/generator.py`)**: Wrote an autonomous Python script capable of generating thousands of compliant `.txt` rules and `.xml` invoices featuring randomized mathematical logic, future dates, and realistic payload sizes to prove platform scalability.

---

### 5. Methodology & Tech Stack

**Frontend (Client)**:
- **React.js 18** + **Vite**: For lightning-fast component rendering and HMR.
- **Tailwind CSS v4**: For semantic utility styling and dynamic theming.
- **Framer Motion**: For buttery-smooth page transitions, modal popups, and micro-animations.
- **Recharts**: For enterprise-grade data visualization.

**Backend (Server)**:
- **Python 3.11** + **FastAPI**: For high-performance, asynchronous REST API architecture.
- **lxml**: For robust, enterprise-grade XML parsing and XSLT mapping.
- **Uvicorn**: As the ASGI web server.

**Methodology - Deterministic NLP**:
Instead of relying on LLMs (like OpenAI) for the core validation loop—which can hallucinate and cause financial auditing compliance issues—this architecture uses **Semantic Pattern Matching**. It parses natural language using deterministic RegEx mapping arrays. This ensures 100% predictable, auditable, and instant generation of XSLT for financial reporting.

---

### 6. How to Run Locally

You need two terminal windows to run the full stack.

#### **Step 1: Start the FastAPI Backend**
1. Open a terminal and navigate to the backend folder:
   `cd d:/ComplyOS/backend`
2. Activate the virtual environment:
   `.\venv\Scripts\activate` (Windows)
3. Install dependencies (if not already installed):
   `pip install -r requirements.txt`
4. Start the server:
   `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
*(The backend is now running at `http://localhost:8000`)*

#### **Step 2: Start the React Frontend**
1. Open a second terminal and navigate to the frontend folder:
   `cd d:/ComplyOS/frontend`
2. Install dependencies (if not already installed):
   `npm install`
3. Start the Vite development server:
   `npm run dev`
*(The frontend is now running at `http://localhost:5173`)*

#### **Step 3: Test the Pipeline**
1. Open your browser to `http://localhost:5173`.
2. Go to **Rule Templates** and select a template (e.g., "Tax Category is required").
3. In **Rule Studio**, click "Parse Rule".
4. Navigate to **XML Validator**.
5. Select the rule in the dropdown, drag an XML file (from `backend/datasets_output/xml_invoices_test/`) into the dropzone, and click **Run Validation**!
