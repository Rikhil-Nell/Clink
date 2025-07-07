# Clink – Restaurant Analytics & Coupon Strategy

Clink is a data-driven analytics and coupon strategy platform for Indian restaurants. It helps businesses analyze customer behavior, order patterns, and product performance, and generates actionable coupon strategies to increase footfall and customer frequency.

## Features

- **KPI Data Analysis**: Analyze customer, order, and product KPIs
- **Coupon Strategy Generation**: Automated, data-driven coupon recommendations
- **Streamlit Dashboard**: Interactive web app for exploring KPIs and strategies
- **Extensible & Modular**: Clean, scalable Python package structure

## Directory Structure

```
📁 Clink
    📁 .vscode
        ─ launch.json
    📁 archive
        ─ agents.py
        ─ app.py
        ─ test.py
        ─ websearch.py
    📁 src
        📁 agents
            ─ __init__.py
            ─ factory.py
            ─ prompts.py
            ─ schemas.py
        📁 analysis
            📁 notebooks
                ─ customer_analysis.ipynb
                ─ order_analysis.ipynb
                ─ product_analysis.ipynb
            ─ __init__.py
            ─ customer_analysis.py
            ─ order_analysis.py
            ─ product_analysis.py
        📁 app
            📁 page
                ─ coupon_generation_page.py
                ─ data_upload_page.py
                ─ kpi_analysis_page.py
            📁 utils
                ─ overview.py
                ─ session.py
                ─ styling.py
            ─ __init__.py
            ─ app.py
        📁 prompts
            📁 analysis_summary
                ─ customer_prompt.txt
                ─ order_prompt.txt
                ─ product_prompt.txt
            📁 standard_coupon
                ─ customer_prompt.txt
                ─ order_prompt.txt
                ─ product_prompt.txt
            ─ chat.txt
            ─ creative_coupon.txt
        📁 results
            📁 customer_analysis
                ─ Customer_KPIs_KnownPhonesOnly.csv
                ─ Customer_KPIs_KnownPhonesOnly.txt
            📁 order_analysis
                ─ Invoice_Aggregation.csv
                ─ Product_Co_occurrence_Top30.csv
            📁 product_analysis
                📁 daily
                    ─ Average_Performance_By_DayOfWeek.csv
                    ─ Daily_Item_Sales_Pivot.csv
                    ─ Daily_Product_Performance.csv
                📁 hourly
                    ─ Average_Performance_By_Hour.csv
                    ─ Hourly_Item_Sales_Pivot.csv
                    ─ Hourly_Product_Performance.csv
                📁 monthly
                    ─ Monthly_Product_Performance.csv
                    ─ Monthly_Top_Selling_Items.csv
                📁 yearly
                    ─ Yearly_Product_Performance.csv
                    ─ Yearly_Top_Selling_Items.csv
        📁 summarization
            ─ __init__.py
            ─ customer_kpi_summarization.py
            ─ order_kpi_summarization.py
            ─ product_kpi_summarization.py
        📁 test data
            ─ Year Order Item Data.csv
            ─ Year Order Item Data.txt
            ─ Year Order Item Data.xlsx
        📁 utils
            ─ __init__.py
            ─ data_loader.py
        ─ __init__.py
        ─ config.py
        ─ settings.py
    📁 summary_json
        ─ customer_kpis_summary.json
        ─ order_kpis_summary.json
    ─ .env
    ─ .gitignore
    ─ .python-version
    ─ Directory Structure.md
    ─ mcp.ps1
    ─ pyproject.toml
    ─ README.md
    ─ requirements.txt
    ─ uv.lock
```

## Getting Started

### Prerequisites

- Python 3.10+ recommended
- pip for package management

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Clink
   ```

2. **Set up a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   
   **Using uv (recommended for speed):**
   ```bash
   uv sync
   ```
   
   **Or using pip:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your .env file** with the required API keys (see .env.example if provided).

## Running the App

**With pip/venv:**
```bash
streamlit run .\src\app\app.py
```

**Or with uv:**
```bash
uv run streamlit run .\src\app\app.py
```

The app will open in your browser. Use the sidebar to navigate between data upload, KPI analysis, and coupon generation.

## Usage

1. Upload your restaurant order data (CSV or Excel)
2. Explore KPIs and insights in the dashboard
3. Review and implement recommended coupon strategies

## Contributing

Pull requests and suggestions are welcome! Please open an issue to discuss changes or new features.

## License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.