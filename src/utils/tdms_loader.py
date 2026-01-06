from pathlib import Path
from typing import Any, Tuple

import matplotlib.pyplot as plt
import numpy as np
from nptdms import TdmsFile
from scipy.signal import firwin, lfilter


def _loadscan_tdms(tdms_file_path: Path) -> Tuple[np.ndarray, int, int]:
    """
    Load scan data from a TDMS file.

    Extracts metadata and waveform data, reshapes the waveform into scan data.

    Parameters:
    tdms_file_path (Path): Path to the TDMS file.

    Returns:
    Tuple[np.ndarray, int, int]: Scan data array, size in x direction, samples per scan.
    """

    tdms_file = TdmsFile.read(tdms_file_path)
    # tdms_file.groups()
    metadata_group = tdms_file["Freq_Sampling_SizeX_SizeY"]
    metadata_channel = metadata_group.channels()[0]
    frequency = metadata_channel[:][0]
    sampling_rate = metadata_channel[:][1]
    size_x = int(metadata_channel[:][2])
    # size_y = int(metadata_channel[:][3])
    samples_per_scan = int(sampling_rate / frequency)

    waveform_group = tdms_file["Waveform"]
    raw_data = waveform_group.channels()[0][:]
    scan_data = np.reshape(raw_data, (-1, samples_per_scan))

    return scan_data, size_x, samples_per_scan


def _reshape_raster(scan_data: np.ndarray, size_x: int) -> np.ndarray:
    """
    Reshape scan data into raster format.

    Alternates row direction for even/odd rows to simulate raster scanning.

    Parameters:
    scan_data (np.ndarray): The scan data array.
    size_x (int): Number of columns in the raster.

    Returns:
    np.ndarray: Reshaped raster data.
    """
    raster_rows = []
    for row_index in range(scan_data.shape[0] // size_x):
        row_data = scan_data[size_x * row_index : size_x * (row_index + 1)]
        if row_index % 2 == 1:
            row_data = row_data[::-1]
        raster_rows.append(row_data)
    raster_data = np.array(raster_rows)
    return raster_data


def read_scan_tdms(
    tdms_file_path: Path, raster: bool = False
) -> Tuple[np.ndarray, int, int, int]:
    """
    Read and optionally process scan data from a TDMS file.

    Loads data, downsamples if necessary, and reshapes to raster if requested.

    Parameters:
    tdms_file_path (Path): Path to the TDMS file.
    raster (bool): Whether to reshape data into raster format.

    Returns:
    Tuple[np.ndarray, int, int, int]: Processed scan data, samples per scan, size x, size y.
    """
    scan_data, size_x, samples_per_scan = _loadscan_tdms(tdms_file_path)
    if samples_per_scan > 500:
        samples_per_scan = samples_per_scan // 4
        indices = np.arange(0, len(scan_data[0]), 4)
        scan_data = scan_data[:, indices]
    size_y = scan_data.shape[0] // size_x

    if raster:
        scan_data = _reshape_raster(scan_data, size_x)
    return scan_data, samples_per_scan, size_x, size_y


def reduce_resolution(
    image_data: np.ndarray, downsample_factor: int = 1
) -> np.ndarray:
    """
    Reduce the resolution of image data by downsampling.

    Parameters:
    image_data (np.ndarray): The image data array.
    downsample_factor (int): Factor by which to downsample.

    Returns:
    np.ndarray: Downsampled image data.
    """
    # Take every other row and column (downsample by factor)
    return image_data[::1, ::1, ::downsample_factor]


def extract_features(
    scan_data: np.ndarray,
    time_segment: Any,
    feature_method: str = "mean",
    subtract_background_x: bool = False,
    subtract_background_y: bool = False,
    show_plot: bool = False,
    apply_raster: bool = False,
    size_x: int = 1,
) -> np.ndarray:
    """
    Extract features from scan data over a specified time segment.

    Applies optional raster reshaping, computes features using the specified method,
    subtracts background if requested, and optionally plots the result.

    Parameters:
    scan_data (np.ndarray): The scan data array.
    time_segment (Any): Time segment to extract features from (e.g., slice or indices).
    feature_method (str): Method to compute features ('mean', 'abs', 'max', 'rms', 'std').
    subtract_background_x (bool): Whether to subtract background along x-axis.
    subtract_background_y (bool): Whether to subtract background along y-axis.
    show_plot (bool): Whether to display a plot of the features.
    apply_raster (bool): Whether to apply raster reshaping.
    size_x (int): Size in x direction for raster reshaping.

    Returns:
    np.ndarray: Extracted features.
    """
    # scan_data = (scan_data)/(scan_data.max())
    if apply_raster:
        scan_data = _reshape_raster(scan_data, size_x)
    if feature_method == "abs":
        features = np.mean(np.abs(scan_data[:, :, time_segment]), axis=2)
    elif feature_method == "max":
        features = np.max(scan_data[:, :, time_segment], axis=2)
    elif feature_method == "rms":
        features = np.mean(scan_data[:, :, time_segment] ** 2, axis=2)
    elif feature_method == "std":
        features = np.std(scan_data[:, :, time_segment], axis=2)
    else:  # mean
        features = np.mean(scan_data[:, :, time_segment], axis=2)

    if subtract_background_x:
        features = features - features[:, 0][:, None]
    if subtract_background_y:
        features = features - features[0, :][None, :]

    if show_plot:
        plt.figure()
        plt.imshow(features, cmap="jet", interpolation="bilinear")
        plt.show()
    return features


def normalize_img(image: np.ndarray) -> np.ndarray:
    """
    Normalize an image array to the range [0, 1].

    Parameters:
    image (np.ndarray): The image array to normalize.

    Returns:
    np.ndarray: Normalized image array.
    """
    image_min, image_max = np.min(image), np.max(image)
    return (image - image_min) / (image_max - image_min + 1e-8)


def _LPF(
    signal: np.ndarray, cutoff_frequency: float = 0.04, filter_order: int = 24
) -> np.ndarray | Any | tuple:
    """
    Apply a low-pass FIR filter to a signal.

    Parameters:
    signal (np.ndarray): The input signal.
    cutoff_frequency (float): Normalized cutoff frequency.
    filter_order (int): Order of the FIR filter.

    Returns:
    np.ndarray: Filtered signal.
    """

    # BUG: not exist lowpass for pass_zero
    b = firwin(
        filter_order + 1,
        cutoff_frequency,
        window="hamming",
        # pass_zero="lowpass",
    )
    signal = np.pad(
        signal, (50, 50), "constant", constant_values=(signal[0], signal[-1])
    )
    filtered_signal = lfilter(b, 1.0, signal)
    filtered_signal = filtered_signal[
        50 + filter_order // 2 : -50 + filter_order // 2
    ]
    return filtered_signal


def LPF_2D(
    data_2d: np.ndarray, cutoff_frequency: float = 0.04, filter_order: int = 24
) -> np.ndarray:
    """
    Apply low-pass filtering to 2D data by filtering each element.

    Parameters:
    data_2d (np.ndarray): 2D array of signals to filter.
    cutoff_frequency (float): Normalized cutoff frequency.
    filter_order (int): Order of the FIR filter.

    Returns:
    np.ndarray: 2D array of filtered signals.
    """
    filtered_signals = []
    for row in range(data_2d.shape[0]):
        for col in range(data_2d.shape[1]):
            filtered = _LPF(data_2d[row, col], cutoff_frequency, filter_order)
            filtered_signals.append(filtered)
    filtered_signals = np.array(filtered_signals)
    filtered_signals = filtered_signals.reshape(
        (data_2d.shape[0], data_2d.shape[1], -1)
    )
    return filtered_signals
