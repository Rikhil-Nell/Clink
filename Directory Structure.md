```
📁 MoM-Analysis
    📁 src
        📁 analysis
            📁 notebooks
                ─ customer_analysis.ipynb
                ─ order_analysis.ipynb
                ─ product_analysis.ipynb
            ─ customer_analysis.py
            ─ order_analysis.py
            ─ product_analysis.py
        📁 prompts
            📁 analysis summary prompts
                ─ customer_analysis_summary_prompt.txt
                ─ order_analysis_summary_prompt.txt
                ─ product_analysis_summary_prompt.txt
            📁 standard coupon prompts
                ─ customer_standard_coupon.txt
                ─ order_standard_coupon.txt
                ─ product _standard_coupon.txt
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
            ─ customer_kpi_summarization.py
            ─ order_kpis_summarization.py
            ─ product_kpi_summarization.py
        📁 test data
            ─ Year Order Item Data.csv
            ─ Year Order Item Data.txt
            ─ Year Order Item Data.xlsx
        📁 utils
            ─ data_loader.py
        ─ __init__.py
        ─ agents.py
        ─ app.py
        ─ config.py
        ─ settings.py
        ─ test.py
        ─ tools.py
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