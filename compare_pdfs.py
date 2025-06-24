import json
import logging
from pathlib import Path
from typing import Union
from deepdiff import DeepDiff
from docling.document_converter import DocumentConverter

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

def compare_pdfs(pdf1_path: Union[str, Path], pdf2_path: Union[str, Path], output_json_path: Union[str, Path] = "output.json") -> None:
    """
    Compare two PDF files and save the differences in JSON format.
    
    Args:
        pdf1_path: Path to the first PDF file.
        pdf2_path: Path to the second PDF file.
        output_json_path: Path to save the JSON output of differences.
    """
    # Create output directory
    output_dir = Path("scratch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert both PDFs to JSON
    json1 = convert_pdf_to_json(pdf1_path, output_dir)
    json2 = convert_pdf_to_json(pdf2_path, output_dir)
    
    # Compare JSONs using DeepDiff
    diff = DeepDiff(json1, json2, ignore_order=True, report_repetition=True)
    
    # Prepare output
    diff_output = {
        "pdf1": str(pdf1_path),
        "pdf2": str(pdf2_path),
        "differences": diff.to_dict() if diff else "No differences found"
    }
    
    # Save differences to output.json
    with Path(output_json_path).open("w", encoding="utf-8") as fp:
        json.dump(diff_output, fp, indent=2)
    
    print(f"Differences saved to {output_json_path}")

def main():
    # Example usage
    pdf1_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\file1.pdf"
    pdf2_path = "D:\\NewWork\\Sandbox\\Python\\comparePDF\\docling\\file2.pdf"
    output_json_path = "output.json"
    
    compare_pdfs(pdf1_path, pdf2_path, output_json_path)

if __name__ == "__main__":
    main()
