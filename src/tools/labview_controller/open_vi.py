#!/usr/bin/env python3
"""
Script to open and optionally run a LabVIEW VI.
This script is intended to be called as a subprocess from labview_controller.py
"""

import sys
from loguru import logger

try:
    import win32com.client  # type: ignore
except ImportError:
    win32com = None


def parse_arguments():
    """Parse command line arguments to determine if the VI should be run and get the VI path."""
    run_vi = "--no-run" not in sys.argv
    log = "--no-log" not in sys.argv

    # Find the VI path (skip the script name and any flags)
    vi_path = None
    for arg in sys.argv[1:]:  # Skip script name
        if not arg.startswith("-"):  # First non-flag argument is the VI path
            vi_path = arg
            break

    if vi_path is None:
        raise ValueError("VI path must be provided as a command line argument.")

    return run_vi, vi_path, log


def open_and_run_vi(vi_path, run_vi, log: bool = True):
    """Open the specified VI and optionally run it."""
    if log:
        logger.info(f"Attempting to open VI: {vi_path}, run: {run_vi}")
    if win32com is None:
        raise ImportError(
            "win32com is required but not available on this platform."
        )

    # Connect to LabVIEW application
    labview_app = win32com.client.Dispatch("LabVIEW.Application")

    # Open the VI
    vi_reference = labview_app.GetVIReference(vi_path)

    # Open the front panel
    vi_reference.FPWinOpen = True

    # Run the VI if requested
    if run_vi:
        vi_reference.Run()

    if log:
        logger.info(f"Successfully opened VI: {vi_path}")
        if run_vi:
            logger.info("VI is now running")
        else:
            logger.info("VI is open but not running")


def main(run_vi=True, vi_path=None, log: bool = True):
    """Main function to open and run the VI."""
    try:
        if vi_path is None:
            raise ValueError("VI path must be provided.")
        open_and_run_vi(vi_path, run_vi, log=log)
    except Exception as e:
        if log:
            logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_vi, vi_path, log = parse_arguments()
    main(run_vi=run_vi, vi_path=vi_path, log=log)
