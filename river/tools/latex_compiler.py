import subprocess
import shutil
from pathlib import Path
from loguru import logger


def tool_compile_latex_to_pdf(
    main_tex_path: Path = Path("latex/main.tex"),
    build_dir: Path = Path("latex/build"),
    output_pdf_path: Path = Path("REPORTING/output.pdf"),
) -> None:
    """
    Compile a LaTeX document to PDF using latexmk and copy the result to the output path.

    This function ensures the build directory exists, runs latexmk to compile the PDF,
    and copies the output to the specified location. It logs key operations and handles
    errors robustly.

    Args:
        main_tex_path: Path to the main LaTeX file, relative to the REPORTING directory.
        build_dir: Directory where latexmk places build files, relative to REPORTING.
        output_pdf_path: Absolute or relative path where the final PDF is copied.

    Raises:
        RuntimeError: If LaTeX compilation fails or file operations encounter issues.
    """
    logger.info("Starting LaTeX compilation for {}", main_tex_path)

    reporting_dir = Path("REPORTING")
    build_path = reporting_dir / build_dir
    output_path = output_pdf_path

    # Ensure build directory exists
    build_path.mkdir(parents=True, exist_ok=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run latexmk to compile the PDF
    command = [
        "latexmk",
        "-pdf",
        "-cd",
        f"-outdir={str(build_dir)}",
        str(main_tex_path),
    ]
    logger.debug("Running command: {} in {}", command, reporting_dir)
    result = subprocess.run(
        command,
        cwd=reporting_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("LaTeX compilation failed: {}", result.stderr)
        raise RuntimeError(f"LaTeX compilation failed: {result.stderr}")

    # Copy the compiled PDF to the output location
    compiled_pdf = build_path / f"{main_tex_path.stem}.pdf"
    if not compiled_pdf.exists():
        error_msg = f"Compiled PDF not found at {compiled_pdf}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    shutil.copy(compiled_pdf, output_path)
    logger.info(
        "LaTeX compilation completed successfully, PDF copied to {}",
        output_path,
    )
