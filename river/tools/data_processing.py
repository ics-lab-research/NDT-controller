import numpy as np
from loguru import logger
from nptdms import TdmsFile
from pathlib import Path
from sklearn.model_selection import train_test_split


def reshape_raster(data: np.ndarray, sX: int) -> np.ndarray:
    """
    Reshapes 1D acquisition order data into a 2D raster map.

    Reverses every other row to correct for raster scanning direction.

    Args:
        data: 2D array of shape (total_points, features).
        sX: Number of points per row in the raster.

    Returns:
        Reshaped 2D array of shape (rows, sX, features).
    """
    logger.info(
        "Starting reshape_raster with data shape {} and sX {}",
        data.shape,
        sX,
    )
    try:
        arr = []
        num_rows = data.shape[0] // sX
        for i in range(num_rows):
            xi = data[sX * i : sX * (i + 1)]
            if i % 2 == 1:
                xi = xi[::-1]
            arr.append(xi)
        reshaped_data = np.array(arr)
        logger.info(
            "Completed reshape_raster, output shape {}",
            reshaped_data.shape,
        )
        return reshaped_data
    except Exception as e:
        logger.error("Error in reshape_raster: {}", e)
        raise


def loadscan_tdms(file: Path) -> tuple[np.ndarray, int, int]:
    """
    Loads scan data from a TDMS file.

    Extracts frequency, sampling rate, sizes, and reshapes waveform data.

    Args:
        file: Path to the TDMS file.

    Returns:
        Tuple of (X_scan: reshaped waveform data, sX: x-size, samples: number of samples per scan).
    """
    logger.info("Starting loadscan_tdms for file {}", file)
    try:
        tdms_file = TdmsFile.read(str(file))
        group1 = tdms_file["Freq_Sampling_SizeX_SizeY"]
        info_channel = group1.channels()[0]
        info_data = info_channel[:]
        frequency = info_data[0]
        sampling_rate = info_data[1]
        sX = int(info_data[2])
        sY = int(info_data[3])  # Not used in return, but extracted
        samples = int(sampling_rate / frequency)

        group2 = tdms_file["Waveform"]
        waveform_data = group2.channels()[0][:]
        X_scan = np.reshape(waveform_data, (-1, samples))

        logger.info(
            "Completed loadscan_tdms, X_scan shape {}, sX {}, samples {}",
            X_scan.shape,
            sX,
            samples,
        )
        return X_scan, sX, samples
    except Exception as e:
        logger.error("Error in loadscan_tdms for file {}: {}", file, e)
        raise


def tool_read_scan_tdms(
    file: Path, raster: bool = False
) -> tuple[np.ndarray, int, int, int]:
    """
    Reads and processes scan data from a TDMS file.

    Loads data, optionally downsamples if samples > 500, calculates sY, and optionally reshapes to raster.

    Args:
        file: Path to the TDMS file.
        raster: If True, reshape to 2D raster map.

    Returns:
        Tuple of (processed_data, samples, sX, sY).
    """
    logger.info("Starting read_scan_tdms for file {}, raster {}", file, raster)
    try:
        # Load raw data and metadata
        data, sX, samples = loadscan_tdms(file)

        # Downsample if necessary
        if samples > 500:
            samples = samples // 4
            idx = np.arange(0, data.shape[1], 4)
            data = data[:, idx]

        # Calculate y-size
        sY = data.shape[0] // sX

        # Reshape to raster if requested
        if raster:
            data = reshape_raster(data, sX)

        logger.info(
            "Completed read_scan_tdms, data shape {}, samples {}, sX {}, sY {}",
            data.shape,
            samples,
            sX,
            sY,
        )
        return data, samples, sX, sY
    except Exception as e:
        logger.error("Error in read_scan_tdms for file {}: {}", file, e)
        raise


def load_train_test_data(
    corroded_file: Path,
    healthy_file: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Loads corroded and healthy TDMS files, assigns labels, and splits into train/test sets.

    Corroded samples are labeled as 1 (anomaly), healthy as 0 (normal).

    Args:
        corroded_file: Path to the corroded TDMS file.
        healthy_file: Path to the healthy TDMS file.
        test_size: Fraction of data to use for testing (default 0.2).
        random_state: Random state for reproducible splitting.

    Returns:
        Tuple of (X_train, y_train, X_test, y_test).
    """
    logger.info(
        "Starting load_train_test_data with corroded_file {} and healthy_file {}",
        corroded_file,
        healthy_file,
    )
    try:
        # Load corroded data and assign label 1
        X_corroded, _, _ = loadscan_tdms(corroded_file)
        y_corroded = np.ones(X_corroded.shape[0], dtype=int)

        # Load healthy data and assign label 0
        X_healthy, _, _ = loadscan_tdms(healthy_file)
        y_healthy = np.zeros(X_healthy.shape[0], dtype=int)

        # Combine data
        X = np.concatenate([X_corroded, X_healthy], axis=0)
        y = np.concatenate([y_corroded, y_healthy], axis=0)

        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        logger.info(
            "Completed load_train_test_data: X_train shape {}, y_train shape {}, X_test shape {}, y_test shape {}",
            X_train.shape,
            y_train.shape,
            X_test.shape,
            y_test.shape,
        )
        return X_train, y_train, X_test, y_test
    except Exception as e:
        logger.error("Error in load_train_test_data: {}", e)
        raise


def extract_features(
    data: np.ndarray,
    segment: range,
    method: str = "mean",
    sub_bg_x: bool = False,
    sub_bg_y: bool = False,
    plot: bool = False,
) -> np.ndarray:
    """
    Extracts features from 2D data over a specified segment.

    Args:
        data: 2D array (e.g., raster map).
        segment: Range of indices for feature extraction.
        method: Feature type ('mean', 'max', 'rms', 'std').
        sub_bg_x: Subtract background along x-axis.
        sub_bg_y: Subtract background along y-axis.
        plot: If True, display plot (requires matplotlib).

    Returns:
        2D feature array.
    """
    if method == "abs":
        x_features = np.mean(np.abs(data[:, :, segment]), axis=2)
    elif method == "max":
        x_features = np.max(data[:, :, segment], axis=2)
    elif method == "rms":
        x_features = np.mean(data[:, :, segment] ** 2, axis=2) ** 0.5
    elif method == "std":
        x_features = np.std(data[:, :, segment], axis=2)
    else:  # mean
        x_features = np.mean(data[:, :, segment], axis=2)

    if sub_bg_x:
        x_features = x_features - x_features[:, 0][:, None]
    if sub_bg_y:
        x_features = x_features - x_features[0, :][None, :]

    if plot:
        import matplotlib.pyplot as plt

        plt.figure()
        plt.imshow(x_features, cmap="jet", interpolation="bilinear")
        plt.show()
    return x_features


def standard_norm(
    X_train: np.ndarray,
    X_scan: np.ndarray,
    axis: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Standardizes data by subtracting mean and dividing by std.

    Args:
        X_train: Training data.
        X_scan: Scan data.
        axis: Axis for normalization.

    Returns:
        Tuple of (normalized_X_train, normalized_X_scan, mean, std).
    """
    m = np.mean(X_train, axis=axis, keepdims=True)
    st = np.std(X_train, axis=axis, keepdims=True) + 1e-9
    X_train_norm = (X_train - m) / st
    X_scan_norm = (X_scan - m) / st
    return X_train_norm, X_scan_norm, m, st


def prepare_detection_data(
    file_path: Path,
    corrosion_points: list | None = None,
    segment_range: tuple = (250, 320),
    method: str = "mean",
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare train/test data for binary detection (corrosion vs. healthy).

    Loads a TDMS scan, separates corrosion/healthy areas via masks, extracts features,
    assigns labels (1 for corrosion, 0 for healthy), normalizes, and splits data.

    Args:
        file_path (Path): Path to TDMS file with mixed scan data.
        corrosion_points (list, optional): List of [x, y, radius] for corrosion circles.
            Defaults to predefined points from river/gui/dataloader.py.
        segment_range (tuple): Sample range for feature extraction (e.g., (250, 320)).
        method (str): Feature method ('mean', 'std', etc.).
        test_size (float): Fraction for test split (0.0-1.0).
        random_state (int): Random seed for reproducibility.

    Returns:
        tuple: (X_train, y_train, X_test, y_test) - Features and binary labels.

    Raises:
        ValueError: If data loading or shapes fail.
        FileNotFoundError: If TDMS file is missing.
    """
    logger.info("Starting detection data preparation for file: {}", file_path)

    # Default corrosion points (from river/gui/dataloader.py, e.g., for collusion scans)
    if corrosion_points is None:
        corrosion_points = [
            [15, 12, 8],
            [15, 73, 6],
            [15, 133, 5],
            [75, 12, 5],
            [75, 73, 5],
            [75, 133, 5],
            [134, 12, 5],
            [134, 73, 5],
            [134, 133, 5],
        ]

    try:
        # Load and reshape scan data
        X_scan, sX, samples = loadscan_tdms(file_path)
        X_org = reshape_raster(X_scan, sX).squeeze()
        logger.info(
            "Loaded scan: shape={}, sX={}, samples={}", X_org.shape, sX, samples
        )

        # Define mask function (pure, from river/gui/dataloader.py)
        def circle_mask(
            px: int, py: int, r: int, data: np.ndarray
        ) -> np.ndarray:
            mask = data.copy()  # Immutable copy
            for x in range(max(0, px - r), min(data.shape[0], px + r)):
                for y in range(max(0, py - r), min(data.shape[1], py + r)):
                    if (x - px) ** 2 + (y - py) ** 2 <= r**2:
                        mask[x, y] = 0
            return mask

        # Separate ground (healthy) and corrosion
        X_ground = X_org.copy()
        for point in corrosion_points:
            X_ground = circle_mask(point[0], point[1], point[2], X_ground)
        X_corrosion = X_org - X_ground  # Anomalous areas

        # Extract features and filter non-zero points
        feat_ground = extract_features(
            X_ground, range(*segment_range), method=method
        )
        feat_corrosion = extract_features(
            X_corrosion, range(*segment_range), method=method
        )

        X_healthy = X_ground[feat_ground != 0].reshape(-1, samples, 1)
        X_anomalous = X_corrosion[feat_corrosion != 0].reshape(-1, samples, 1)

        # Assign labels and combine
        y_healthy = np.zeros(len(X_healthy), dtype=int)
        y_anomalous = np.ones(len(X_anomalous), dtype=int)
        X_full = np.concatenate([X_healthy, X_anomalous])
        y_full = np.concatenate([y_healthy, y_anomalous])

        # Normalize and split
        X_full, _, _, _ = standard_norm(
            X_full, X_full
        )  # Normalize in-place on copy
        X_train, X_test, y_train, y_test = train_test_split(
            X_full,
            y_full,
            test_size=test_size,
            stratify=y_full,
            random_state=random_state,
        )

        logger.info(
            "Prepared data: X_train shape={}, y_train shape={}, classes balanced",
            X_train.shape,
            y_train.shape,
        )
        return X_train, y_train, X_test, y_test

    except FileNotFoundError:
        logger.error("TDMS file not found: {}", file_path)
        raise
    except Exception as e:
        logger.error("Error in data preparation: {}", str(e))
        raise ValueError(f"Data preparation failed: {str(e)}")
