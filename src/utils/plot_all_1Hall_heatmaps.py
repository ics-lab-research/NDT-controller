#%% ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from nptdms import TdmsFile
import dataloader

np.random.seed(1)

#%% Configuration ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Folder containing TDMS files
data_folder = '/work/huy.leminh/code/Dr.Huy/PECT/Data/Duong/basic'

# Output folder for saving plots
output_folder = os.path.join(data_folder, 'heatmap_plots')
os.makedirs(output_folder, exist_ok=True)

# Processing parameters
# slice_window = range(15, 30)  # Window for slice feature extraction
# loi_window = range(15, 22)    # Window for LOI feature extraction
# peak_window = range(0, 100)   # Window for peak feature extraction

slice_window = range(0, 50)  # Window for slice feature extraction
loi_window = range(20, 30)    # Window for LOI feature extraction
peak_window = range(0, 499)   # Window for peak feature extraction

# Filter parameters
lpf_cutoff = 0.04
lpf_order = 24

#%% Get all TDMS files ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Get all TDMS files (excluding index files and PECT_default.tdms)
tdms_files = glob.glob(os.path.join(data_folder, '*.tdms'))
tdms_files = [f for f in tdms_files if not f.endswith('_index') and not f.endswith('PECT_default.tdms')]
tdms_files.sort()

print(f"Found {len(tdms_files)} TDMS files:")
for i, file in enumerate(tdms_files):
    print(f"  {i+1}. {os.path.basename(file)}")

#%% Process each TDMS file ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

plt.rc('font', size=24)  # Set default text size for all elements

for tdms_file in tdms_files:
    filename = os.path.basename(tdms_file)
    print(f"\nProcessing: {filename}")
    
    try:
        # Load and preprocess scan data
        data, samples, sX, sY = dataloader.read_scan_tdms(tdms_file, raster=True)
        data = dataloader.reduce_resolution(data)
        data -= np.mean(data, axis=2, keepdims=True)
        
        # Apply Low-Pass Filter
        data = data - data[:, :, :1]
        X_filter = dataloader.LPF_2D(data, cutoff=lpf_cutoff, order=lpf_order)
        X_filter -= np.mean(X_filter, axis=2, keepdims=True)
        
        # ========================================
        # 1. SLICE - Extract features from raw filtered data
        # ========================================
        X_feat_slice = dataloader.extract_features(
            X_filter, 
            slice_window, 
            method='abs', 
            sub_bg_x=False, 
            sub_bg_y=False, 
            plot=False
        )
        
        # ========================================
        # 2. LOI - Extract features from gradient data
        # ========================================
        X_filter_grad = np.diff(X_filter, axis=2)
        X_feat_loi = dataloader.extract_features(
            X_filter_grad, 
            loi_window, 
            method='abs', 
            sub_bg_x=False, 
            sub_bg_y=False, 
            plot=False
        )
        
        # ========================================
        # 3. PEAK - Extract max features from gradient data
        # ========================================
        X_feat_peak = dataloader.extract_features(
            X_filter_grad, 
            peak_window, 
            method='max', 
            sub_bg_x=False, 
            sub_bg_y=False, 
            plot=False
        )
        
        # ========================================
        # Plot all three heatmaps in one figure
        # ========================================
        fig = plt.figure(figsize=(24, 8))
        
        # Slice
        plt.subplot(1, 3, 1)
        plt.imshow(dataloader.normalize_img(X_feat_slice), cmap='jet', interpolation='bilinear')
        plt.clim(0, 0.9)
        plt.title('Slice Feature Map')
        plt.xlabel('X-direction [mm]')
        plt.ylabel('Y-direction [mm]')
        plt.colorbar()
        
        # LOI
        plt.subplot(1, 3, 2)
        plt.imshow(dataloader.normalize_img(X_feat_loi), cmap='jet', interpolation='bilinear')
        plt.clim(0, 0.9)
        plt.title('LOI Feature Map')
        plt.xlabel('X-direction [mm]')
        plt.ylabel('Y-direction [mm]')
        plt.colorbar()
        
        # Peak
        plt.subplot(1, 3, 3)
        plt.imshow(dataloader.normalize_img(X_feat_peak), cmap='jet', interpolation='bilinear')
        plt.clim(0, 0.9)
        plt.title('Peak Feature Map')
        plt.xlabel('X-direction [mm]')
        plt.ylabel('Y-direction [mm]')
        plt.colorbar()
        
        plt.tight_layout()
        
        # Save figure
        output_filename = os.path.splitext(filename)[0] + '_heatmaps.png'
        output_path = os.path.join(output_folder, output_filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"  Saved: {output_filename}")
        
        plt.show()
        plt.close()
        
    except Exception as e:
        print(f"  ERROR processing {filename}: {str(e)}")
        continue

print(f"\n✓ All plots saved to: {output_folder}")

#%% Generate a summary comparison plot (optional) ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# If you want to compare all files in a grid
print("\nGenerating summary comparison plot...")

n_files = len(tdms_files)
if n_files > 0:
    fig = plt.figure(figsize=(24, 8 * n_files))
    
    for idx, tdms_file in enumerate(tdms_files):
        filename = os.path.basename(tdms_file)
        print(f"  Adding {filename} to summary...")
        
        try:
            # Load and process
            data, samples, sX, sY = dataloader.read_scan_tdms(tdms_file, raster=True)
            data = dataloader.reduce_resolution(data)
            data -= np.mean(data, axis=2, keepdims=True)
            
            data = data - data[:, :, :1]
            X_filter = dataloader.LPF_2D(data, cutoff=lpf_cutoff, order=lpf_order)
            X_filter -= np.mean(X_filter, axis=2, keepdims=True)
            
            # Extract features
            X_feat_slice = dataloader.extract_features(X_filter, slice_window, method='abs', sub_bg_x=False, sub_bg_y=False, plot=False)
            X_filter_grad = np.diff(X_filter, axis=2)
            X_feat_loi = dataloader.extract_features(X_filter_grad, loi_window, method='abs', sub_bg_x=False, sub_bg_y=False, plot=False)
            X_feat_peak = dataloader.extract_features(X_filter_grad, peak_window, method='max', sub_bg_x=False, sub_bg_y=False, plot=False)
            
            # Plot
            plt.subplot(n_files, 3, idx * 3 + 1)
            plt.imshow(dataloader.normalize_img(X_feat_slice), cmap='jet', interpolation='bilinear')
            plt.clim(0, 0.9)
            if idx == 0:
                plt.title('Slice Feature Map', fontsize=20)
            plt.ylabel(filename.replace('.tdms', '').replace('_', ' '), fontsize=14)
            plt.axis('off')
            
            plt.subplot(n_files, 3, idx * 3 + 2)
            plt.imshow(dataloader.normalize_img(X_feat_loi), cmap='jet', interpolation='bilinear')
            plt.clim(0, 0.9)
            if idx == 0:
                plt.title('LOI Feature Map', fontsize=20)
            plt.axis('off')
            
            plt.subplot(n_files, 3, idx * 3 + 3)
            plt.imshow(dataloader.normalize_img(X_feat_peak), cmap='jet', interpolation='bilinear')
            plt.clim(0, 0.9)
            if idx == 0:
                plt.title('Peak Feature Map', fontsize=20)
            plt.axis('off')
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            continue
    
    plt.tight_layout()
    summary_path = os.path.join(output_folder, 'all_files_comparison.png')
    plt.savefig(summary_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Summary comparison saved to: {summary_path}")
    plt.show()
    plt.close()

print("\n✓ Done!")

# %%
