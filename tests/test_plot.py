from pathlib import Path
from src.utils.heatmap_plotter import generate_heatmaps

if __name__ == "__main__":
    data_file = Path(
        "EXPERIMENT/data/corosion_frontside_chirp_100x100_500-1500Hz_2.97_20260105_111327.tdms"
    )

    output_folder = Path("EXPERIMENT/plots/")

    generate_heatmaps(
        tdms_file=data_file,
        experiment_id="96afddef-02b8-4e30-9dc4-077b4f4baff7",
        output_folder=output_folder,
    )
