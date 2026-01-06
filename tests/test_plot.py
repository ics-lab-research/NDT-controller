from pathlib import Path
from src.utils.heatmap_plotter import generate_heatmaps

if __name__ == "__main__":
    data_folder = Path("EXPERIMENT/data")

    generate_heatmaps(data_folder)
