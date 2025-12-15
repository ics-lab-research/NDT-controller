# %% ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os, glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from nptdms import TdmsFile
import numpy as np
from scipy.signal import butter, lfilter, freqz, firwin

# from scipy.signal import butter, lfilter, freqz, firwin, gaussian
from scipy import signal
from sklearn.model_selection import train_test_split
import h5py
import scipy.io
# %% Filters ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def butter_lowpass_filter(data, cutoff=0.04, fs=1, order=4):
    b, a = butter(order, cutoff, fs=fs, btype="low", analog=False)
    y = lfilter(b, a, data)
    return y


def LPF_butter(X_train, cutoff=0.04, fs=1, order=4):
    X = []
    for x in X_train:
        x = butter_lowpass_filter(x, cutoff, fs, order)
        X.append(x)
    X = np.array(X)[:, :, None]
    return X


def LPF(X_train, cutoff=0.04, order=24):
    X = []
    for x in X_train.squeeze():
        x = np.pad(x, (50, 50), "constant", constant_values=(x[0], x[-1]))
        # b = firwin(order+1, cutoff, window = ('gaussian', len(x)), pass_zero = False)
        b = firwin(order + 1, cutoff, window="hamming", pass_zero=False)
        x = lfilter(b, 1.0, x)
        x = x[50 + order // 2 : -50 + order // 2]
        X.append(x)

    X = np.array(X)[:, :, None]
    return X


def BPF(x, fl=0.7, fh=0.9, order=24):
    b = firwin(
        order + 1, [fl, fh], window=("gaussian", order / 5), pass_zero=False
    )
    y = lfilter(b, 1.0, x - np.mean(x))
    return y


def filter_2D(X, fl=500, fh=1500, fs=100000):
    Y = []
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            y = BPF(X[i, j], fl / fs, fh / fs, order=24)
            Y.append(y)
    Y = np.array(Y)
    Y = Y.reshape((X.shape[0], X.shape[1], -1))
    return Y


def filter_1D(X, cutoff=0.04, norm=True):
    X = X - np.mean(X)
    X = LPF_butter(X[None, :], cutoff=cutoff, fs=1, order=2)
    if norm:
        X = norm01(X, axis=(1))
    return X.squeeze()


# %% Previos methods ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def diff_method(data, cutoff=0.04, order=2):
    # paper: Pulsed Eddy Current Technology: Characterizing Material Loss with Gap and Lift-off Variations
    # data: N x samples
    # x = norm01(data, axis=(1))
    x = np.diff(data, axis=1)
    x = LPF_butter(x, cutoff=cutoff, fs=1, order=order).squeeze()
    return x


def norm_method(data, air, ref_id=None, cutoff=0.04, order=2):
    # paper: Reduction of lift-off effects for pulsed eddy current NDT
    # data: N x samples including ref at ref_id
    # data = norm01(data, axis=(1))
    # air = norm01(air, axis=(1))
    x = air - data
    x = LPF_butter(x, cutoff=cutoff, fs=1, order=order).squeeze()
    x = norm01(x, axis=(1))
    if ref_id is not None:
        x = x - x[ref_id : ref_id + 1]  # subtract ref
    return x


# %% ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def running_avr(x, alpha, c):
    # alpha = 2/(N+1)
    c = alpha * x + (1 - alpha) * c  # c will be modified
    y = x - c
    return y, c


def running_avr_2D(x, alpha, c):
    # x = scan_data[2]
    # N = 10
    # alpha = 2/(N+1)
    data_c = np.zeros(x.shape[0])
    y = []
    for i in range(x.shape[1]):
        data_ravr, data_c = running_avr(x[:, i], alpha, data_c)
        y.append(data_ravr)
    y = np.array(y).T

    plt.imshow(x, cmap="jet", interpolation="bilinear")
    plt.show()
    plt.imshow(y[:, N:], cmap="jet", interpolation="bilinear")
    plt.show()

    return y


# %% 1D to 2D RASTER SCAN MAPPING ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def reshape_raster(data, sX):
    arr = []
    for i in range(data.shape[0] // sX):
        xi = data[sX * i : sX * (i + 1)]
        if i % 2 == 1:
            xi = xi[::-1]
        arr.append(xi)
    data = np.array(arr)
    return data


# %% NORM ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def offset(x, axis=(1, 2, 3)):
    val_mean = np.mean(x, axis=axis, keepdims=True)
    y = x - val_mean

    return y


def norm01(X_train, axis=(1, 2, 3)):
    val_max = np.max(X_train, axis=axis, keepdims=True)
    val_min = np.min(X_train, axis=axis, keepdims=True)
    X_train = (X_train - val_min) / (val_max - val_min)

    return X_train


def standard_norm(X_train, X_scan, axis=0):
    m = np.mean(X_train, axis=axis, keepdims=True)
    st = np.std(X_train, axis=axis, keepdims=True) + 1e-9
    X_train -= m
    X_train /= st
    X_scan -= m
    X_scan /= st
    return X_train, X_scan, m, st


# def standard_norm_snn(X_train, X_valid, X_scan, Xc, Xg, X_in_corr, y_train, y_valid, axis=0, snn = True):
#     m = np.mean(X_train,axis = axis, keepdims=True)
#     st = np.std(X_train,axis = axis, keepdims=True) + 1e-9
#     X_train -= m;    X_train /= st
#     X_valid -= m;    X_valid /= st
#     X_scan -= m;    X_scan /= st
#     Xc -= m;    Xc /= st
#     Xg -= m;    Xg /= st
#     for k in X_in_corr.keys():
#         X_in_corr[k] -= m;    X_in_corr[k] /= st

#     if snn:
#         # flatten data and add time dimension
#         X_train = X_train.reshape((X_train.shape[0], 1, -1))
#         y_train = y_train.reshape((y_train.shape[0], 1, -1))
#         X_valid = X_valid.reshape((X_valid.shape[0], 1, -1))
#         y_valid = y_valid.reshape((y_valid.shape[0], 1, -1))
#         X_scan = X_scan.reshape((X_scan.shape[0], 1, -1))
#         Xc = Xc.reshape((Xc.shape[0], 1, -1))
#         Xg = Xg.reshape((Xg.shape[0], 1, -1))


#     return X_train, y_train, X_valid, y_valid, X_scan, m, st, X_in_corr, Xc, Xg
def standard_norm_snn(
    X_train,
    X_valid,
    X_scan,
    Xc,
    Xg,
    X_in_corr,
    y_train,
    y_valid,
    axis=0,
    snn=True,
):
    # Tính mean và std theo trục đã chọn
    m = np.mean(X_train, axis=axis, keepdims=True)
    st = np.std(X_train, axis=axis, keepdims=True) + 1e-9

    # Nếu shape có 3 chiều thì reshape mean/std để broadcast đúng
    if X_train.ndim == 3:
        # (samples, features, channels)
        m = m.reshape((1, X_train.shape[1], X_train.shape[2]))
        st = st.reshape((1, X_train.shape[1], X_train.shape[2]))
    elif X_train.ndim == 2:
        # (samples, features)
        m = m.reshape((1, X_train.shape[1]))
        st = st.reshape((1, X_train.shape[1]))

    # Áp dụng chuẩn hóa cho các tập
    X_train = (X_train - m) / st
    X_valid = (X_valid - m) / st
    X_scan = (X_scan - m) / st
    Xc = (Xc - m.squeeze()) / st.squeeze()
    Xg = (Xg - m.squeeze()) / st.squeeze()

    # Chuẩn hóa từng key trong X_in_corr
    if isinstance(X_in_corr, dict):
        for k in X_in_corr:
            X_in_corr[k] = (X_in_corr[k] - m.squeeze()) / st.squeeze()

    # Nếu snn=True thì reshape thêm chiều thời gian
    if snn:

        def snn_reshape(x):
            return x.reshape((x.shape[0], 1, -1))

        X_train = snn_reshape(X_train)
        y_train = snn_reshape(y_train)
        X_valid = snn_reshape(X_valid)
        y_valid = snn_reshape(y_valid)
        X_scan = snn_reshape(X_scan)
        Xc = snn_reshape(Xc)
        Xg = snn_reshape(Xg)

    return X_train, y_train, X_valid, y_valid, X_scan, m, st, X_in_corr, Xc, Xg


def de_standard_norm(X, m, st):
    X *= st
    X += m
    return X


def self_minmax(X_train, X_scan, axis=(1, 2, 3)):
    val_max = np.max(X_train, axis=axis, keepdims=True)
    val_min = np.min(X_train, axis=axis, keepdims=True)
    X_train = (X_train - val_min) / (val_max - val_min)

    val_max = np.max(X_scan, axis=axis, keepdims=True)
    val_min = np.min(X_scan, axis=axis, keepdims=True)
    X_scan = (X_scan - val_min) / (val_max - val_min)

    return X_train, X_scan


def segment(X_train, w=5, s=1):
    N = (len(X_train) - w) // s + 1
    X = []
    for i in range(N):
        X.append(X_train[i * s : i * s + w].reshape(-1))
    X = np.array(X)
    X = X[:, :, None]
    return X


def desegment(X, w=5, s=1):
    X2 = []
    for i in range(len(X)):
        X2.append(X[i].reshape(w, -1)[:s])
    X2 = np.array(X2)
    X2 = X2.reshape(-1, X2.shape[-1])
    X2 = np.concatenate([X2, X[i].reshape(w, -1)[s:]])
    return X2


# %% TRAINING DATA ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def load_csv(path):
    # path = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off2'
    path_list = os.listdir(path)
    files = list(
        filter(lambda f: f.endswith(".csv") and f.startswith("no"), path_list)
    )
    x_no = []
    for file in files:
        temp = pd.read_csv(
            os.path.join(path, file), index_col=None, header=None
        )
        x_no.append(temp)
    x_no = pd.concat(x_no, axis=0, ignore_index=True).to_numpy()

    files = list(
        filter(lambda f: f.endswith(".csv") and f.startswith("d"), path_list)
    )
    x_c = []
    for file in files:
        temp = pd.read_csv(
            os.path.join(path, file), index_col=None, header=None
        )
        x_c.append(temp)
    x_c = pd.concat(x_c, axis=0, ignore_index=True).to_numpy()

    X_train = x_no[:, :, None]
    X_test = x_c[:, :, None]

    return X_train, X_test


# %% SCAN DATA ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def loadscan_tdms(file):
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz30x90.tdms'
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz150x150v3.tdms'

    tdms_file = TdmsFile.read(file)
    # tdms_file.groups()
    group1 = tdms_file["Freq_Sampling_SizeX_SizeY"]
    infor = group1.channels()[0]
    f = infor[:][0]
    sampling = infor[:][1]
    sX = int(infor[:][2])
    sY = int(infor[:][3])
    samples = int(sampling / f)

    group2 = tdms_file["Waveform"]
    data = group2.channels()[0][:]
    X_scan = np.reshape(data, (-1, samples))

    return X_scan, sX, samples


def read_scan_tdms(file, raster=False):
    data, sX, samples = loadscan_tdms(file)
    if samples > 500:
        samples = samples // 4
        idx = np.arange(0, len(data[0]), 4)
        data = data[:, idx]
    sY = data.shape[0] // sX

    if raster:
        data = reshape_raster(data, sX)
    return data, samples, sX, sY


def loadscan_tdms_train_test(file):
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz30x90.tdms'
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz150x150v3.tdms'
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off_2.0\PECT_collusion_150x150.tdms'

    tdms_file = TdmsFile.read(file)
    # tdms_file.groups()
    group1 = tdms_file["Freq_Sampling_SizeX_SizeY"]
    infor = group1.channels()[0]
    f = infor[:][0]
    sampling = infor[:][1]
    sX = int(infor[:][2])
    sY = int(infor[:][3])
    samples = int(sampling / f)

    group2 = tdms_file["Waveform"]
    data = group2.channels()[0][:]
    X_scan = np.reshape(data, (-1, samples))
    # ids = 90*sX; idn = 120*sX
    ids = 30 * sX
    idn = 60 * sX
    X_no1 = X_scan[ids:idn, :]
    ids = 90 * sX
    idn = 120 * sX
    X_no2 = X_scan[ids:idn, :]
    ids = 140 * sX
    idn = 150 * sX
    X_no3 = X_scan[ids:idn, :]
    X_no = np.concatenate([X_no2, X_no3])

    X_no = X_no[:, :, None]
    X_scan = X_scan[:, :, None]

    x = reshape_raster(np.reshape(data, (-1, samples)), sX)
    X_features = np.mean(x[:, :, :50], axis=2)

    # plt.figure()
    # plt.imshow(X_features, cmap='jet',interpolation='bilinear')
    # plt.colorbar()
    # plt.show()

    return X_no, X_scan, X_features, sX, samples


def loadsteel_tdms_train_test(file):
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\Scan steel\step_0.5_Steel_Basic_front_160x110.tdms'

    X_scan, sX, samples = loadscan_tdms(file)
    if samples > 500:
        samples = samples // 4
        idx = np.arange(0, len(X_scan[0]), 4)
        X_scan = X_scan[:, idx]

    ids = 0 * sX
    idn = 50 * sX
    X_no1 = X_scan[ids:idn, :]
    ids = 60 * sX
    idn = 90 * sX
    X_no2 = X_scan[ids:idn, :]
    ids = 120 * sX
    idn = 140 * sX
    X_no3 = X_scan[ids:idn, :]
    ids = 170 * sX
    idn = 220 * sX
    X_no4 = X_scan[ids:idn, :]
    X_no = np.concatenate([X_no1, X_no2, X_no3, X_no4])

    X_no = X_no[:, :, None]
    X_scan = X_scan[:, :, None]

    x = reshape_raster(X_scan, sX)
    X_features = np.mean(x[:, :, :50], axis=2)

    plt.figure()
    plt.imshow(
        X_features, cmap="jet", vmax=2.0, vmin=1.0, interpolation="bilinear"
    )
    plt.colorbar()
    plt.show()

    return X_no, X_scan, X_features, sX, samples


def loadscan_tdms_nomal_anomal(file, idsx, idnx):
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz30x90.tdms'
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off\step_1_f_200_amp_2.0_sz150x150v3.tdms'
    # file = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data\on_off_2.0\PECT_collusion_150x150.tdms'

    X_scan, sX, samples = loadscan_tdms(file)
    if samples > 500:
        samples = samples // 4
        idx = np.arange(0, len(X_scan[0]), 4)
        X_scan = X_scan[:, idx]

    # idsx = [30,90,145]
    # idnx = [60,120,150]
    X_no = []
    for i in range(len(idsx)):
        ids = idsx[i] * sX
        idn = idnx[i] * sX
        x = X_scan[ids:idn, :]
        X_no.append(x)
    X_no = np.concatenate(X_no)

    X_no = X_no[:, :, None]
    X_scan = X_scan[:, :, None]

    return X_no, X_scan, sX, samples


def scan_features_plot(data, sX, segment, method="mean", do_raster=True):
    # data is a list of 2D array (N,samples)
    plt.figure(figsize=(5, 12))
    for i in range(len(data)):
        plt.subplot(len(data), 1, i + 1)
        if do_raster:
            x = reshape_raster(data[i], sX)
        else:
            x = data[i]

        # x = data[i].reshape(-1,sX,512,1)
        if method == "abs":
            x_features = np.mean(np.abs(x[:, :, segment]), axis=2)
        elif method == "rms":
            x_features = np.mean(x[:, :, segment] ** 2, axis=2) ** 0.5
        elif method == "std":
            x_features = np.std(x[:, :, segment], axis=2)
        else:  # mean
            x_features = np.mean(x[:, :, segment], axis=2)

        plt.imshow(x_features[:120, :], cmap="jet", interpolation="bilinear")
        plt.colorbar()
        plt.xticks([])
        plt.yticks([])
    plt.show()


def scan_features_plot_hor(data, sX, segment, method="mean", do_raster=True):
    # data is a list of 2D array (N,samples)
    plt.figure(figsize=(12, 4))
    for i in range(len(data)):
        plt.subplot(1, len(data), i + 1)
        if do_raster:
            x = reshape_raster(data[i], sX)
        else:
            x = data[i]

        # x = data[i].reshape(-1,sX,512,1)
        if method == "abs":
            x_features = np.mean(np.abs(x[:, :, segment]), axis=2)
        elif method == "rms":
            x_features = np.mean(x[:, :, segment] ** 2, axis=2) ** 0.5
        elif method == "std":
            x_features = np.std(x[:, :, segment], axis=2)
        else:  # mean
            x_features = np.mean(x[:, :, segment], axis=2)

        plt.imshow(x_features[:120, :], cmap="jet", interpolation="bilinear")
        plt.colorbar()
        plt.xticks([])
        plt.yticks([])
    plt.show()


def extract_features(
    data, segment, method="mean", sub_bg_x=False, sub_bg_y=False, plot=False
):
    if method == "abs":
        x_features = np.mean(np.abs(data[:, :, segment]), axis=2)
    elif method == "max":
        x_features = np.max(data[:, :, segment], axis=2)
    elif method == "rms":
        x_features = np.mean(data[:, :, segment] ** 2, axis=2)
    elif method == "std":
        x_features = np.std(data[:, :, segment], axis=2)
    else:  # mean
        x_features = np.mean(data[:, :, segment], axis=2)

    if sub_bg_x:
        x_features = x_features - x_features[:, 0][:, None]
    if sub_bg_y:
        x_features = x_features - x_features[0, :][None, :]

    if plot:
        plt.figure()
        plt.imshow(x_features, cmap="jet", interpolation="bilinear")
        plt.show()
    return x_features


def plot_img(x_features):
    plt.figure()
    plt.imshow(x_features, cmap="jet", interpolation="bilinear")
    plt.show()


def load_nomal_anomal():
    # folder = 'D:\OneDrive - Phenikaa Univesity\RESEARCH DIRECTIONS\AI NDT\PECT\Data'
    parent_dir = os.path.split(os.getcwd())[0]
    folder = parent_dir + "\Data"

    files = []
    idsx = []
    idnx = []

    # files.append('\San 9 Colusiom 30_5_23\step_0.5_AL_basic_front_160x160.tdms')
    # # idsx.append([60,180,300]); idnx.append([140,260,320])
    # idsx.append([70,180]); idnx.append([140,260])

    # files.append('\San 9 Colusiom 30_5_23\step_0.5_AL_basic_behind_160x160.tdms')
    # # idsx.append([60,180,300]); idnx.append([140,260,320])
    # idsx.append([70,180]); idnx.append([140,260])

    files.append("\Scan 9 Colusiom\Colusion_basic_front.tdms")
    # idsx.append([30,90,140]); idnx.append([60,120,150])
    idsx.append([90, 140])
    idnx.append([120, 150])

    files.append("\on_off_2.0\PECT_collusion_150x150.tdms")
    # idsx.append([30,90,140]); idnx.append([60,120,150])
    idsx.append([90, 140])
    idnx.append([120, 150])

    # files.append('\San 9 Colusiom 30_5_23\step_0.5_AL_basic_behind_160x160.tdms')
    # # idsx.append([70,185,300]); idnx.append([130,260,320])
    # idsx.append([185,300]); idnx.append([260,320])

    X_no = []
    X_scan = []
    sX = []
    samples = []
    for i in range(len(files)):
        file = files[i]
        ids = idsx[i]
        idn = idnx[i]
        X_no_i, X_scan_i, sX_i, samples_i = loadscan_tdms_nomal_anomal(
            folder + file, ids, idn
        )
        X_no.append(X_no_i)
        X_scan.append(X_scan_i)
        sX.append(sX_i)
        samples.append(samples_i)

    return X_no, X_scan, sX, samples


# % Data for classification model ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def load_data_cls():
    # % SCAN DATA ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    _, X_scan, sX, samples = load_nomal_anomal()

    # % Scan data ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    no_data = 0
    X_scan = X_scan[no_data]
    sX = sX[no_data]
    samples = samples[no_data]

    print("Scan size: ", X_scan.shape)

    # % ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    X_org = reshape_raster(X_scan, sX).squeeze()

    # % Separate Corrosion and Background ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # function to return a matrix with points within a circle having center at (px, py) and radius r, the other points are set to zero

    def circle_mask(px, py, r, X):
        # X could be 2D (feature) or 3D (raw)
        mask = X.copy()
        for x in range(px - r, px + r):
            for y in range(py - r, py + r):
                if (x - px) ** 2 + (y - py) ** 2 <= r**2:
                    mask[x, y] = 0
        return mask

    # P = [[15,12,8],[15,73,6],[15,133,5],[75,12,5],[75,73,5],[75,133,5]]
    # P = [[15,12,8],[15,73,6],[15,133,5],[75,12,5],[75,73,5],[75,133,5],[134,12,5],[134,73,5],[134,133,5]]
    P = [
        [75, 12, 5],
        [75, 73, 5],
        [75, 133, 5],
        [134, 12, 5],
        [134, 73, 5],
        [134, 133, 5],
    ]

    # Raw pulse
    X_ground = []
    X_corrosion = []

    # a = X_org[:120,:]
    a = X_org
    x = a
    for pi in P:
        x = circle_mask(pi[0], pi[1], pi[2], x)
    X_ground = x
    X_corrosion = a - x

    X_ground_feat = extract_features(
        X_ground,
        range(250, 320),
        method="mean",
        sub_bg_x=False,
        sub_bg_y=False,
        plot=False,
    )
    X_corrosion_feat = extract_features(
        X_corrosion,
        range(250, 320),
        method="mean",
        sub_bg_x=False,
        sub_bg_y=False,
        plot=False,
    )

    plt.figure(figsize=(6, 10))
    plt.subplot(3, 1, 1)
    plt.imshow(X_ground_feat, cmap="jet", interpolation="bilinear")
    plt.colorbar()
    plt.title(" ")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(3, 1, 2)
    plt.imshow(X_corrosion_feat, cmap="jet", interpolation="bilinear")
    plt.colorbar()
    plt.title(" ")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(3, 1, 3)
    plt.imshow(
        X_ground_feat + X_corrosion_feat, cmap="jet", interpolation="bilinear"
    )
    plt.colorbar()
    plt.title(" ")
    plt.xticks([])
    plt.yticks([])
    plt.show()

    # %

    X_ground = X_ground[50:, :]
    Xg = X_ground[X_ground_feat[50:, :] != 0]
    Xc = X_corrosion[X_corrosion_feat != 0]
    yg = np.array([0] * len(Xg))
    yc = np.array([1] * len(Xc))
    X = np.concatenate([Xg, Xc])
    X = X[:, :, None]
    y = np.concatenate([yg, yc])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=42, test_size=0.2, stratify=y
    )

    return X_train, X_test, y_train, y_test


def convert_stft(X, nperseg=8, nfft=256, scaling="psd"):
    Z = []
    for i in range(len(X)):
        f, t, z = signal.stft(
            X[i], 1, nperseg=nperseg, nfft=nfft, scaling=scaling
        )
        Z.append(np.abs(z))
        if i % 10000 == 0:
            # print i with percentage
            print(f" {100 * i / len(X)} %")
    Z = np.array(Z)
    return Z


def get_train_dataset(file):
    # folder = '/hoinghi/dataset/dataset'
    # folder = "E:/OneDrive/Papers 2025/Domestic Confer/Uncertainty PECT/dataset/"

    # file = [folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_basic_front_160x160.tdms',
    #         folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_gaussian_front_160x160.tdms',
    #         folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_chirp_front_160x160.tdms',
    #         ]

    # file = [folder + '/Scan 9 Colusiom/Colusion_basic_front.tdms',
    #         folder + '/Scan 9 Colusiom/Colusion_gaussian_front_4V.tdms',
    #         folder + '/Scan 9 Colusiom/Colusion_chirp_front.tdms',
    #         ]

    X_scan, sX, samples = loadscan_tdms(file[1])
    if samples > 500:
        samples = samples // 4
        X_scan = X_scan[:, np.arange(0, len(X_scan[0]), 4)]

    print("Scan size: ", X_scan.shape)

    # % ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    X_org = reshape_raster(X_scan, sX).squeeze()

    # % Separate Corrosion and Background ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # function to return a matrix with points within a circle having center at (px, py) and radius r, the other points are set to zero

    def circle_mask(px, py, r, X):
        # X could be 2D (feature) or 3D (raw)
        mask = X.copy()
        for x in range(px - r, px + r):
            for y in range(py - r, py + r):
                if (x - px) ** 2 + (y - py) ** 2 <= r**2:
                    mask[x, y] = 0
        return mask

    # P = [[40,38,10],[40,158,10],[40,278,10],[160,38,10],[160,158,10],[160,278,10],[280,38,10],[280,158,10],[280,278,10]]
    P = [
        [15, 12, 5],
        [15, 73, 5],
        [15, 133, 5],
        [75, 12, 5],
        [75, 73, 5],
        [75, 133, 5],
        [134, 12, 5],
        [134, 73, 5],
        [134, 133, 5],
    ]

    # Raw pulse
    X_ground = []
    X_corrosion = []

    # a = X_org[:120,:]
    a = X_org
    x = a
    for pi in P:
        x = circle_mask(pi[0], pi[1], pi[2], x)
    X_ground = x
    X_corrosion = a - x

    X_ground_feat = extract_features(
        X_ground,
        range(250, 320),
        method="mean",
        sub_bg_x=False,
        sub_bg_y=False,
        plot=False,
    )
    X_corrosion_feat = extract_features(
        X_corrosion,
        range(250, 320),
        method="mean",
        sub_bg_x=False,
        sub_bg_y=False,
        plot=False,
    )

    # plt.figure(figsize=(6, 10))
    # plt.subplot(3,1,1)
    # plt.imshow(X_ground_feat,cmap='jet',interpolation='bilinear')
    # plt.colorbar()
    # plt.title(' ')
    # plt.xticks([])
    # plt.yticks([])

    # plt.subplot(3,1,2)
    # plt.imshow(X_corrosion_feat,cmap='jet',interpolation='bilinear')
    # plt.colorbar()
    # plt.title(' ')
    # plt.xticks([])
    # plt.yticks([])

    # plt.subplot(3,1,3)
    # plt.imshow(X_ground_feat + X_corrosion_feat,cmap='jet',interpolation='bilinear')
    # plt.colorbar()
    # plt.title(' ')
    # plt.xticks([])
    # plt.yticks([])
    # plt.show()

    # %

    Xc = X_corrosion[X_corrosion_feat != 0]
    Xg = X_ground[X_ground_feat != 0]
    # return random elements in array Xg same with number of elemnts in Xc
    # Xg = Xg[np.random.choice(len(Xg),len(Xc)*2,replace=False)]

    yg = np.array([0] * len(Xg))
    yc = np.array([1] * len(Xc))
    X = np.concatenate([Xg, Xc])
    X = X[:, :, None]
    y = np.concatenate([yg, yc])

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, random_state=42, test_size=0.4, stratify=y
    )
    X_scan = X_scan[:, :, None]

    print("Train, Scan: ", X_train.shape, X_valid.shape)
    print(y_train.shape, y_valid.shape)

    # scipy.io.savemat("train_data.mat", {
    #         "X_train": X_train,
    #         "y_train": y_train,
    #         "label_names": ["no crack", "crack"],  # Thêm tên nhãn
    #         "X_scan": X_scan,
    #         "sX": sX,
    #         "samples": samples
    #         })
    # scipy.io.savemat("valid_data.mat", {
    #         "X_valid": X_valid,
    #         "y_valid": y_valid,
    #         "label_names": ["no crack", "crack"]  # Thêm tên nhãn
    #         })
    # return X_train, y_train, X_valid, y_valid, X_scan, sX, samples
    return (
        X_train,
        y_train,
        X_valid,
        y_valid,
        X_scan,
        sX,
        samples,
        Xc,
        Xg,
        X_corrosion,
    )


# get_train_dataset()
# def get_train_dataset_stft(gendata = True):
#    if gendata:
#        folder = '/hoinghi/dataset/dataset'

# file = [folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_basic_front_160x160.tdms',
#         folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_gaussian_front_160x160.tdms',
#         folder + '/San 9 Colusiom 30_5_23/step_0.5_AL_chirp_front_160x160.tdms',
#         ]

#       file = [folder + '/Scan 9 Colusiom/Colusion_basic_front.tdms',
#                folder + '/Scan 9 Colusiom/Colusion_gaussian_front_4V.tdms',
#                folder + '/Scan 9 Colusiom/Colusion_chirp_front.tdms',
#                ]
#
#        X_scan, sX, samples = loadscan_tdms(file[1])
#        if samples > 500:
#            samples = samples//4
#            X_scan = X_scan[:,np.arange(0,len(X_scan[0]),4)]
#
#        print('Scan size: ', X_scan.shape)

# % ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#        X_org = reshape_raster(X_scan,sX).squeeze()

# % Separate Corrosion and Background ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# function to return a matrix with points within a circle having center at (px, py) and radius r, the other points are set to zero

#        def circle_mask(px, py, r, X):
#            # X could be 2D (feature) or 3D (raw)
#            mask = X.copy()
#            for x in range(px-r, px+r):
#                for y in range(py-r, py+r):
#                    if (x-px)**2 + (y-py)**2 <= r**2:
#                        mask[x,y] = 0
#            return mask

#        def get_in_circle(px, py, r, X):
# X could be 2D (feature) or 3D (raw)
#            a = []
#            for x in range(px-r, px+r):
#                for y in range(py-r, py+r):
#                    if (x-px)**2 + (y-py)**2 <= r**2:
#                        a.append(X[x,y])
#            return np.array(a)

# P = [[40,38,10],[40,158,10],[40,278,10],[160,38,10],[160,158,10],[160,278,10],[280,38,10],[280,158,10],[280,278,10]]
#        P = [[15,12,5],[15,73,5],[15,133,5],[75,12,5],[75,73,5],[75,133,5],[134,12,5],[134,73,5],[134,133,5]]
# P = [[15,12,5],[15,73,5]]
#        num = [7, 8, 9, 4, 5, 6, 1, 2, 3]
#        d = np.array([0.86, 0.66, 0.48, 0.84, 0.65, 0.44, 0.78, 0.60, 0.40])
#        dia = np.array([10, 10, 10, 8, 8, 8, 6, 6, 6])
#        V = 3.14*d*dia**2/4

#       X_in_corr = {}
#        for i,pi in enumerate(P):
# dictionary with index in num
#            X_in_corr['num_'+str(num[i])] = get_in_circle(pi[0],pi[1],pi[2],X_org)

# Raw pulse
#        X_ground = []
#        X_corrosion = []

# a = X_org[:120,:]
#        a = X_org
#        x = a
#        for pi in P:
#            x = circle_mask(pi[0],pi[1],pi[2],x)
#        X_ground = x
#        X_corrosion = a-x


#        X_ground_feat = extract_features(X_ground,range(250,320),method='mean',sub_bg_x=False,sub_bg_y=False,plot=False)
#        X_corrosion_feat = extract_features(X_corrosion,range(250,320),method='mean',sub_bg_x=False,sub_bg_y=False,plot=False)


#        plt.figure(figsize=(6, 10))
#        plt.subplot(3,1,1)
#        plt.imshow(X_ground_feat,cmap='jet',interpolation='bilinear')
#        plt.colorbar()
#        plt.title(' ')
#        plt.xticks([])
#        plt.yticks([])

#        plt.subplot(3,1,2)
#        plt.imshow(X_corrosion_feat,cmap='jet',interpolation='bilinear')
#        plt.colorbar()
#        plt.title(' ')
#        plt.xticks([])
#        plt.yticks([])

#        plt.subplot(3,1,3)
#        plt.imshow(X_ground_feat + X_corrosion_feat,cmap='jet',interpolation='bilinear')
#        plt.colorbar()
#        plt.title(' ')
#        plt.xticks([])
#        plt.yticks([])
#        plt.show()


#        Xc = X_corrosion[X_corrosion_feat!=0]
#        Xg = X_ground[X_ground_feat!=0]
# return random elements in array Xg same with number of elemnts in Xc
# Xg = Xg[np.random.choice(len(Xg),len(Xc)*2,replace=False)]

#        Xg = convert_stft(Xg, nperseg=16, nfft=128, scaling='spectrum')
#        Xc = convert_stft(Xc, nperseg=16, nfft=128, scaling='spectrum')
#        X_scan = convert_stft(X_scan.squeeze(), nperseg=16, nfft=128, scaling='spectrum')

#        for i in num:
#            X_in_corr['num_'+str(i)] = convert_stft(X_in_corr['num_'+str(i)], nperseg=16, nfft=128, scaling='spectrum')
#            X_in_corr['num_'+str(i)] = X_in_corr['num_'+str(i)][:,:,:,None]

# plt.figure(figsize=(6, 10))
# plt.subplot(3,1,1)
# plt.imshow(Xg[0],cmap='jet',interpolation='bilinear')
# plt.colorbar()
# plt.title(' ')
# plt.xticks([])
# plt.yticks([])

# plt.subplot(3,1,2)
# plt.imshow(Xc[0],cmap='jet',interpolation='bilinear')
# plt.colorbar()
# plt.title(' ')
# plt.xticks([])
# plt.yticks([])

# plt.subplot(3,1,3)
# plt.imshow(Xc[0]-Xg[0],cmap='jet',interpolation='bilinear')
# plt.colorbar()
# plt.title(' ')
# plt.xticks([])
# plt.yticks([])

#        yg = np.array([0]*len(Xg))
#        yc = np.array([1]*len(Xc))
#        X = np.concatenate([Xg,Xc]); X = X[:,:,:,None]
#        y = np.concatenate([yg,yc])

#        X_train, X_valid, y_train, y_valid = train_test_split(X, y, random_state=42, test_size=0.4, stratify=y)
#        X_scan = X_scan[:,:,:,None]
#        Xc = Xc[:,:,:,None]
#        Xg = Xg[:,:,:,None]
#        nc, ng = len(yc), len(yg)
#        print('Train, Scan: ', X_train.shape, X_valid.shape)

# save X_train, y_train, X_valid, y_valid, X_scan, sX, samples, len(yc), len(yg) to hdf5 file
#        with h5py.File('dataset.h5', 'w') as f: # dataset_square.h5 for square pulse
#            f.create_dataset('X_train', data=X_train)
#            f.create_dataset('y_train', data=y_train)
#            f.create_dataset('X_valid', data=X_valid)
#            f.create_dataset('y_valid', data=y_valid)
#            f.create_dataset('X_scan', data=X_scan)
#            f.create_dataset('Xc', data=Xc)
#            f.create_dataset('Xg', data=Xg)
#            f.create_dataset('sX', data=sX)
#            f.create_dataset('samples', data=samples)
#            f.create_dataset('nc', data=nc)
#            f.create_dataset('ng', data=ng)

#            f.create_dataset('V', data=V)
#            f.create_dataset('num', data=num)
#            f.create_dataset('d', data=d)
#            f.create_dataset('dia', data=dia)
# convert keys to array
#            keys = list(X_in_corr.keys())
#            string_dtype = h5py.string_dtype(encoding="utf-8")
#            f.create_dataset('X_in_corr_key', data=keys,dtype=string_dtype)

#            for key, value in X_in_corr.items():
#                f.create_dataset(key, data=value)


#    else:
# read from hdf5 file
#        with h5py.File('dataset.h5', 'r') as f: # dataset_square.h5 for square pulse
#            X_train = f['X_train'][()]
#           y_train = f['y_train'][()]
#            X_valid = f['X_valid'][()]
#            y_valid = f['y_valid'][()]
#            X_scan = f['X_scan'][()]
#            Xc = f['Xc'][()]
#            Xg = f['Xg'][()]
#            sX = f['sX'][()]
#            samples = f['samples'][()]
#            nc = f['nc'][()]
#            ng = f['ng'][()]

#            V = f['V'][()]
#            num = f['num'][()]
#            d = f['d'][()]
#            dia = f['dia'][()]
#            keys = f['X_in_corr_key'][()]
#            keys = [k.decode('utf-8') for k in keys]
#            X_in_corr = {}
#            for key in keys:
#                X_in_corr[key] = f[key][()]

#    return X_train, y_train, X_valid, y_valid, X_scan, Xc, Xg, sX, samples, nc, ng, X_in_corr, V, num, d, dia

# save X_train,
