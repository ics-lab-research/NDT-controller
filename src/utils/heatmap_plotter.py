from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from .tdms_loader import (
    LPF_2D,
    extract_features,
    normalize_img,
    read_scan_tdms,
    reduce_resolution,
)

np.random.seed(1)


def get_tdms_files(data_folder: Path) -> List[Path]:
    """Retrieve and filter TDMS files from the data folder."""
    logger.info("Retrieving TDMS files")
    tdms_files = list(data_folder.glob("*.tdms"))
    tdms_files = [
        f
        for f in tdms_files
        if not str(f).endswith("_index")
        and not str(f).endswith("PECT_default.tdms")
    ]
    tdms_files.sort()
    logger.info(f"Found {len(tdms_files)} TDMS files")
    return tdms_files


def process_tdms_file(
    tdms_file: Path,
    slice_window: range,
    loi_window: range,
    peak_window: range,
    lpf_cutoff: float,
    lpf_order: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Process a single TDMS file and extract features."""
    logger.info(f"Processing file: {tdms_file.name}")
    data, samples, sX, sY = read_scan_tdms(tdms_file, raster=True)
    data = reduce_resolution(data)
    data -= np.mean(data, axis=2, keepdims=True)

    data = data - data[:, :, :1]
    X_filter = LPF_2D(data, lpf_cutoff, lpf_order)
    X_filter -= np.mean(X_filter, axis=2, keepdims=True)

    X_feat_slice = extract_features(
        X_filter,
        slice_window,
        feature_method="abs",
        subtract_background_x=False,
        subtract_background_y=False,
        show_plot=False,
    )

    X_filter_grad = np.diff(X_filter, axis=2)
    X_feat_loi = extract_features(
        X_filter_grad,
        loi_window,
        feature_method="abs",
        subtract_background_x=False,
        subtract_background_y=False,
        show_plot=False,
    )
    X_feat_peak = extract_features(
        X_filter_grad,
        peak_window,
        feature_method="max",
        subtract_background_x=False,
        subtract_background_y=False,
        show_plot=False,
    )
    logger.info(f"Finished processing: {tdms_file.name}")
    return X_feat_slice, X_feat_loi, X_feat_peak


def plot_individual_heatmaps(
    X_feat_slice: np.ndarray,
    X_feat_loi: np.ndarray,
    X_feat_peak: np.ndarray,
    experiment_id: str,
    output_folder: Path,
):
    """Plot and save individual heatmaps for a single file."""
    logger.info(f"Plotting individual heatmaps for experiment: {experiment_id}")
    # fig = plt.figure(figsize=(24, 8))

    plt.subplot(1, 3, 1)
    plt.imshow(
        normalize_img(X_feat_slice), cmap="jet", interpolation="bilinear"
    )
    plt.clim(0, 0.9)
    plt.title("Slice Feature Map")
    plt.xlabel("X-direction [mm]")
    plt.ylabel("Y-direction [mm]")
    plt.colorbar()

    plt.subplot(1, 3, 2)
    plt.imshow(normalize_img(X_feat_loi), cmap="jet", interpolation="bilinear")
    plt.clim(0, 0.9)
    plt.title("LOI Feature Map")
    plt.xlabel("X-direction [mm]")
    plt.ylabel("Y-direction [mm]")
    plt.colorbar()

    plt.subplot(1, 3, 3)
    plt.imshow(normalize_img(X_feat_peak), cmap="jet", interpolation="bilinear")
    plt.clim(0, 0.9)
    plt.title("Peak Feature Map")
    plt.xlabel("X-direction [mm]")
    plt.ylabel("Y-direction [mm]")
    plt.colorbar()

    plt.tight_layout()
    output_filename = experiment_id + ".png"
    output_path = output_folder / output_filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved individual plot: {output_filename}")


def plot_summary_comparison(
    features_list: List[Tuple[np.ndarray, np.ndarray, np.ndarray]],
    tdms_files: List[Path],
    output_folder: Path,
):
    """Plot and save a summary comparison of all files."""
    logger.info("Generating summary comparison plot")
    n_files = len(tdms_files)
    if n_files == 0:
        return
    # fig = plt.figure(figsize=(24, 8 * n_files))

    for idx, (X_feat_slice, X_feat_loi, X_feat_peak) in enumerate(
        features_list
    ):
        filename = tdms_files[idx].name
        logger.info(f"Adding {filename} to summary")

        plt.subplot(n_files, 3, idx * 3 + 1)
        plt.imshow(
            normalize_img(X_feat_slice), cmap="jet", interpolation="bilinear"
        )
        plt.clim(0, 0.9)
        if idx == 0:
            plt.title("Slice Feature Map", fontsize=20)
        plt.ylabel(filename.replace(".tdms", "").replace("_", " "), fontsize=14)
        plt.axis("off")

        plt.subplot(n_files, 3, idx * 3 + 2)
        plt.imshow(
            normalize_img(X_feat_loi), cmap="jet", interpolation="bilinear"
        )
        plt.clim(0, 0.9)
        if idx == 0:
            plt.title("LOI Feature Map", fontsize=20)
        plt.axis("off")

        plt.subplot(n_files, 3, idx * 3 + 3)
        plt.imshow(
            normalize_img(X_feat_peak), cmap="jet", interpolation="bilinear"
        )
        plt.clim(0, 0.9)
        if idx == 0:
            plt.title("Peak Feature Map", fontsize=20)
        plt.axis("off")

    plt.tight_layout()
    summary_path = output_folder / "all_files_comparison.png"
    plt.savefig(summary_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Summary comparison saved to: {summary_path}")


def generate_heatmaps(tdms_file: Path, experiment_id: str, output_folder: Path):
    """Main function to process a TDMS file and generate plots."""
    if not tdms_file.is_file() or not tdms_file.suffix == ".tdms":
        logger.error(f"Provided path is not a valid TDMS file: {tdms_file}")
        return

    output_folder.mkdir(exist_ok=True)

    slice_window = range(0, 50)
    loi_window = range(20, 30)
    peak_window = range(0, 499)
    lpf_cutoff = 0.04
    lpf_order = 24

    plt.rc("font", size=24)

    try:
        features = process_tdms_file(
            tdms_file,
            slice_window,
            loi_window,
            peak_window,
            lpf_cutoff,
            lpf_order,
        )
        plot_individual_heatmaps(*features, experiment_id, output_folder)
    except Exception as e:
        logger.error(f"Error processing {tdms_file.name}: {str(e)}")
        return

    logger.info(f"Plot saved to: {output_folder}")
