from pathlib import Path
from src.utils.heatmap_plotter import generate_heatmaps

if __name__ == "__main__":
    data_file = Path(
        "EXPERIMENT/data/corosion_frontside_gauss_100x100_1000Hz_3.88_3.tdms_20260105_104833.tdms"
    )

    output_folder = Path("EXPERIMENT/plots/")

    generate_heatmaps(
        tdms_file=data_file,
        experiment_id="fdsfafd-fdsf",
        output_folder=output_folder,
    )
