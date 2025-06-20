import pandas as pd
from pathlib import Path
from pydantic_ai import RunContext  # Assuming you're using this in the broader context
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

