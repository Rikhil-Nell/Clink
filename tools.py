import pandas as pd
from pathlib import Path
from pydantic_ai import RunContext
from typing import Dict
from dataclasses import dataclass

@dataclass
class Deps:
    kpi_base_folder: str = "./results"

async def explore_kpi_structure(ctx: RunContext[Deps]) -> str:
    base_path = Path(ctx.deps.kpi_base_folder)

    if not base_path.exists():
        return "KPI base folder not found"

    def scan_directory(path: Path) -> Dict:
        result = {"folders": [], "files": []}
        try:
            for item in path.iterdir():
                if item.is_dir():
                    result["folders"].append({
                        "name": item.name,
                        "content": scan_directory(item)
                    })
                elif item.suffix.lower() == '.csv':
                    result["files"].append(item.name)
        except PermissionError:
            pass
        return result

    structure = scan_directory(base_path)

    def format_structure(struct: Dict, level: int = 0) -> str:
        output = []
        indent = "  " * level
        for folder in struct["folders"]:
            output.append(f"{indent}📁 {folder['name']}/")
            output.append(format_structure(folder["content"], level + 1))
        for file in struct["files"]:
            output.append(f"{indent}📄 {file}")
        return "\n".join(output)

    return f"KPI Folder Structure:\n{format_structure(structure)}"

async def list_kpi_files_by_category(ctx: RunContext[Deps], category: str, subcategory: str = None) -> str:
    base_path = Path(ctx.deps.kpi_base_folder)
    target_path = base_path / category / subcategory if subcategory else base_path / category

    if not target_path.exists():
        return f"Path {target_path} not found"

    csv_files = list(target_path.glob("*.csv"))

    if not csv_files:
        return f"No CSV files found in {target_path}"

    file_info = []
    for file in csv_files:
        try:
            stat = file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            file_info.append(f"  📄 {file.name} ({size_mb:.2f} MB)")
        except Exception:
            file_info.append(f"  📄 {file.name}")

    return f"Files in {category}" + (f"/{subcategory}" if subcategory else "") + f":\n" + "\n".join(file_info)

async def load_kpi_file(ctx: RunContext[Deps], category: str, filename: str, subcategory: str = None) -> str:
    base_path = Path(ctx.deps.kpi_base_folder)
    filepath = base_path / category / subcategory / filename if subcategory else base_path / category / filename

    if not filepath.exists():
        return f"File not found: {filepath}"

    try:
        df = pd.read_csv(filepath)
        summary = f"""
📊 KPI File Analysis
Path: {category}{'/' + subcategory if subcategory else ''}/{filename}
Shape: {df.shape[0]} rows, {df.shape[1]} columns
Columns: {', '.join(df.columns.tolist())}

📋 First 5 rows:
{df.head().to_string()}

📈 Basic Statistics:
{df.describe().to_string()}
        """
        return summary
    except Exception as e:
        return f"Error loading file: {str(e)}"

async def search_kpi_files(ctx: RunContext[Deps], search_term: str) -> str:
    base_path = Path(ctx.deps.kpi_base_folder)
    if not base_path.exists():
        return "KPI base folder not found"

    matches = []

    def search_recursive(path: Path, current_path: str = ""):
        try:
            for item in path.iterdir():
                if item.is_dir():
                    new_path = f"{current_path}/{item.name}" if current_path else item.name
                    search_recursive(item, new_path)
                elif item.suffix.lower() == '.csv' and search_term.lower() in item.name.lower():
                    matches.append(f"{current_path}/{item.name}" if current_path else item.name)
        except PermissionError:
            pass

    search_recursive(base_path)

    if not matches:
        return f"No files found matching '{search_term}'"

    return f"Files matching '{search_term}':\n" + "\n".join([f"  📄 {match}" for match in matches])

async def analyze_time_series_kpi(ctx: RunContext[Deps], category: str, time_period: str, filename: str) -> str:
    base_path = Path(ctx.deps.kpi_base_folder)
    filepath = base_path / category / time_period / filename

    if not filepath.exists():
        return f"File not found: {filepath}"

    try:
        df = pd.read_csv(filepath)

        date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp', 'day', 'month', 'year', 'hour'])]

        analysis = f"""
⏰ Time Series Analysis: {category}/{time_period}/{filename}
Shape: {df.shape[0]} rows, {df.shape[1]} columns

📅 Potential date/time columns: {', '.join(date_cols) if date_cols else 'None detected'}

📊 Summary Statistics:
{df.describe().to_string()}
        """

        if date_cols:
            for col in date_cols[:1]:
                try:
                    df[col] = pd.to_datetime(df[col])
                    analysis += f"\n\n📈 Time range for {col}: {df[col].min()} to {df[col].max()}"
                except Exception:
                    continue

        return analysis
    except Exception as e:
        return f"Error analyzing time series data: {str(e)}"
