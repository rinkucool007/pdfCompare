import json
import logging
from pathlib import Path
from typing import Union, Dict, Any
from datetime import datetime
from deepdiff import DeepDiff
from docling.document_converter import DocumentConverter

def format_differences(differences: Any) -> str:
    """
    Format differences from deepdiff for inclusion in reports.
    
    Args:
        differences: The 'differences' field from deepdiff (dict or str).
    
    Returns:
        A string summarizing the differences.
    """
    if isinstance(differences, str):
        return differences  # e.g., "No differences found"
    
    result = []
    for diff_type, changes in differences.items():
        result.append(f"{diff_type.replace('_', ' ').title()}:")
        for path, change in changes.items():
            result.append(f"  - {path}:")
            if isinstance(change, dict):
                for key, value in change.items():
                    result.append(f"    {key}: {value}")
            else:
                result.append(f"    {change}")
    return "\n".join(result)

def escape_latex(text: str) -> str:
    """
    Escape special characters for LaTeX.
    
    Args:
        text: Input string.
    
    Returns:
        Escaped string suitable for LaTeX.
    """
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    return ''.join(latex_special_chars.get(c, c) for c in text)

def convert_pdf_to_json(pdf_path: Union[str, Path], output_dir: Path) -> dict:
    """
    Convert a PDF file to JSON format using Docling.
    
    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Directory to store temporary files.
    
    Returns:
        Dictionary containing the JSON representation of the PDF content.
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    
    # Initialize DocumentConverter with default settings
    doc_converter = DocumentConverter()
    
    # Convert PDF to document
    input_doc_path = Path(pdf_path)
    _log.info(f"Converting {input_doc_path} to JSON...")
    conv_result = doc_converter.convert(input_doc_path)
    
    # Export to JSON
    doc_filename = conv_result.input.file.stem
    json_output_path = output_dir / f"{doc_filename}.json"
    json_data = conv_result.document.export_to_dict()
    
    with json_output_path.open("w", encoding="utf-8") as fp:
        fp.write(json.dumps(json_data, indent=2))
    
    return json_data

def generate_markdown_report(json_data: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Generate a Markdown report from the JSON comparison data.
    
    Args:
        json_data: Dictionary containing 'pdf1', 'pdf2', and 'differences'.
        output_path: Path to save the Markdown file.
    """
    report = [
        "# PDF Comparison Report",
        f"**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Compared Files",
        f"- **PDF 1**: {json_data.get('pdf1', 'Unknown')}",
        f"- **PDF 2**: {json_data.get('pdf2', 'Unknown')}",
        "",
        "## Differences",
        format_differences(json_data.get('differences', "No data available"))
    ]
    
    with Path(output_path).open("w", encoding="utf-8") as fp:
        fp.write("\n".join(report))

def generate_latex_report(json_data: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Generate a LaTeX report from the JSON comparison data.
    
    Args:
        json_data: Dictionary containing 'pdf1', 'pdf2', and 'differences'.
        output_path: Path to save the LaTeX file.
    """
    latex_content = [
        r"\documentclass[a4paper,12pt]{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{times}",
        r"\usepackage{geometry}",
        r"\geometry{margin=1in}",
        r"\usepackage{parskip}",
        r"\usepackage{enumitem}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}",
        r"\textbf{\Large PDF Comparison Report}",
        r"\vspace{0.5em}",
        r"\textbf{Generated on:} " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        r"\vspace{1em}",
        r"\section*{Compared Files}",
        r"\begin{itemize}",
        r"  \item \textbf{PDF 1:} " + escape_latex(json_data.get('pdf1', 'Unknown')),
        r"  \item \textbf{PDF 2:} " + escape_latex(json_data.get('pdf2', 'Unknown')),
        r"\end{itemize}",
        r"\vspace{1em}",
        r"\section*{Differences}",
        escape_latex(format_differences(json_data.get('differences', "No data available"))).replace("\n", r"\\"),
        r"\end{document}"
    ]
    
    with Path(output_path).open("w", encoding="utf-8") as fp:
        fp.write("\n".join(latex_content))

def compare_and_report(pdf1_path: Union[str, Path], pdf2_path: Union[str, Path], output_json_path: Union[str, Path] = "output.json", output_md_path: Union[str, Path] = "output.md", output_tex_path: Union[str, Path] = "output.tex") -> None:
    """
    Compare two PDF files, save differences in JSON, and generate Markdown and LaTeX reports.
    
    Args:
        pdf1_path: Path to the first PDF file.
        pdf2_path: Path to the second PDF file.
        output_json_path: Path to save the JSON output of differences.
        output_md_path: Path to save the Markdown report.
        output_tex_path: Path to save the LaTeX report (compiles to output.pdf).
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    
    # Verify PDF files exist
    pdf1_path = Path(pdf1_path)
    pdf2_path = Path(pdf2_path)
    if not pdf1_path.exists():
        _log.error(f"PDF file not found: {pdf1_path}")
        return
    if not pdf2_path.exists():
        _log.error(f"PDF file not found: {pdf2_path}")
        return
    
    # Create output directory
    output_dir = Path("scratch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert both PDFs to JSON
    _log.info("Converting PDFs to JSON...")
    json1 = convert_pdf_to_json(pdf1_path, output_dir)
    json2 = convert_pdf_to_json(pdf2_path, output_dir)
    
    # Compare JSONs using DeepDiff
    _log.info("Comparing JSON outputs...")
    diff = DeepDiff(json1, json2, ignore_order=True, report_repetition=True)
    
    # Prepare JSON output
    diff_output = {
        "pdf1": str(pdf1_path),
        "pdf2": str(pdf2_path),
        "differences": diff.to_dict() if diff else "No differences found"
    }
    
    # Save differences to output.json
    with Path(output_json_path).open("w", encoding="utf-8") as fp:
        json.dump(diff_output, fp, indent=2)
    _log.info(f"Differences saved to {output_json_path}")
    
    # Generate reports
    _log.info("Generating Markdown report...")
    generate_markdown_report(diff_output, output_md_path)
    _log.info(f"Markdown report saved to {output_md_path}")
    
    _log.info("Generating LaTeX report...")
    generate_latex_report(diff_output, output_tex_path)
    _log.info(f"LaTeX report saved to {output_tex_path}")

def main():
    # Example usage
    pdf1_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\file1.pdf"
    pdf2_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\file2.pdf"
    output_json_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\output.json"
    output_md_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\output.md"
    output_tex_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\output.tex"
    
    compare_and_report(pdf1_path, pdf2_path, output_json_path, output_md_path, output_tex_path)

if __name__ == "__main__":
    main()
