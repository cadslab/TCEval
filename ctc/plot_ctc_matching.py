import logging
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

# ===================== Logging Configuration (Timestamp in filename & content) =====================
# Automatically create the history directory
LOG_DIR = "history"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generate timestamp for log filename (format: YYYYMMDD_HHMMSS)
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"ctc_plotter_{run_timestamp}.log"
log_file_path = os.path.join(LOG_DIR, log_filename)

# Configure logging: output to console and file, with timestamp and log level
logging.basicConfig(
    level=logging.INFO,
    # Log format: timestamp - log level - message
    format="%(asctime)s - %(levelname)s - %(message)s",
    # Timestamp display format
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler(
            log_file_path,
            encoding="utf-8",
            mode="w",  # Write mode: create a new file for each run
        ),
    ],
)


class CTCHeatmapPlotter:
    """CTC Matching Result Heatmap Plotting Tool"""

    # Configuration parameters (91*91, total elements of target matrix)
    DEFAULT_CONFIG = {
        "figure_dpi": 300,
        "font_family": "Arial",
        "font_size": 12,
        "axes_titlesize": 12,
        "axes_labelsize": 12,
        "base_figure_size": (14, 4.5),
        "grid_hspace": 0.05,
        "grid_wspace": 0.1,
        "colorbar_label": "PMV difference (predicted - base)",
        "output_filename": "ctc_heatmaps.png",
        "matrix_shape": (91, 91),
        "rect_linewidth": 0.5,
        "title_pad": 2,
    }

    def __init__(self, folder_path=".", config=None):
        """Initialize the heatmap plotter"""
        self.folder_path = folder_path
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        self._setup_matplotlib()

        # Data-related attributes
        self.csv_files = []
        self.model_names = []
        self.dataframes = []
        self.global_vmin = None
        self.global_vmax = None

    def _setup_matplotlib(self):
        """Configure matplotlib parameters"""
        plt.rcParams["figure.dpi"] = self.config["figure_dpi"]
        plt.rcParams["font.family"] = self.config["font_family"]
        plt.rcParams["font.size"] = self.config["font_size"]
        plt.rcParams["axes.titlesize"] = self.config["axes_titlesize"]
        plt.rcParams["axes.labelsize"] = self.config["axes_labelsize"]

    def load_data(self):
        """Load and preprocess CSV file data"""
        # Find all CSV files
        self.csv_files = [
            os.path.join(self.folder_path, f)
            for f in os.listdir(self.folder_path)
            if f.lower().endswith(".csv")
        ]

        if not self.csv_files:
            logging.info("No CSV files found")
            return False

        # Extract model names and load data
        self.model_names = [os.path.basename(f).split(".")[0] for f in self.csv_files]
        logging.info(f"Found {len(self.model_names)} models: {self.model_names}")
        self.dataframes = []
        for idx, file in enumerate(self.csv_files):
            df = pd.read_csv(file)
            # Note: Create a copy to avoid modifying the original DataFrame
            df = df.copy()

            # Mark samples that meet special exclusion conditions
            # Define 4 conditions:
            # Condition 1: PMV_float < -3
            cond1 = df["PMV_float"] < -3
            # Condition 2: PMV_float > 3
            cond2 = df["PMV_float"] > 3
            # Condition 3: PMV_string is null (missing value)
            cond3 = df["PMV_string"].isna()
            # Condition 4: PMV_float is null (missing value)
            cond4 = df["PMV_float"].isna()

            # Combine conditions: mark as black if any condition is satisfied
            df["is_black"] = cond1 | cond2 | cond3 | cond4

            # Calculate value differences and string matching results
            df["float_diff"] = df["PMV_float"] - df["PMV_float_base"]
            df["float_diff_abs"] = df["float_diff"].abs()
            df["string_match"] = df["PMV_string_base"] == df["PMV_string"]
            self.dataframes.append(df)

            # Log data statistics
            logging.info(f"[{self.model_names[idx]}] Original data rows: {len(df)}")
            logging.info(
                f"[{self.model_names[idx]}] Matching result rows: {df['string_match'].sum()}"
            )
            logging.info(
                f"[{self.model_names[idx]}] Matching result ratio: {df['string_match'].sum()/len(df):.4f}"
            )

            # Log ratios for multiple thresholds (0.1 to 0.5)
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
            for thresh in thresholds:
                logging.info(
                    f"[{self.model_names[idx]}] Ratio of absolute differences < {thresh}: {df['float_diff_abs'].lt(thresh).sum()/len(df):.4f}"
                )

            logging.info(
                f"[{self.model_names[idx]}] Black marked rows (special conditions): {df['is_black'].sum()}"
            )

        # Calculate global value range for unified heatmap color scale
        all_float_diff = pd.concat([df["float_diff"] for df in self.dataframes])
        self.global_vmin = all_float_diff.min()
        self.global_vmax = all_float_diff.max()
        logging.info(
            f"\nGlobal float_diff range: {self.global_vmin:.4f} ~ {self.global_vmax:.4f}"
        )
        return True

    def _prepare_matrix_data(self, df, model_name):
        """Prepare matrix data (ensure length matches target size)"""
        rows, cols = self.config["matrix_shape"]
        target_size = rows * cols

        # Process string matching results (convert to integer type)
        match_values = df["string_match"].astype(int).values
        # Pad or truncate data to match target matrix size
        if len(match_values) < target_size:
            pad_length = target_size - len(match_values)
            match_values = np.pad(
                match_values, (0, pad_length), "constant", constant_values=0
            )
            logging.info(
                f"[{model_name}] Insufficient matching data, padded {pad_length} zeros (original {len(match_values)-pad_length} → target {target_size})"
            )
        elif len(match_values) > target_size:
            match_values = match_values[:target_size]
            logging.info(
                f"[{model_name}] Excessive matching data, truncated to {target_size} entries (original {len(match_values)} → target {target_size})"
            )

        # Process float difference results
        float_diff_values = df["float_diff"].values
        # Pad or truncate data to match target matrix size
        if len(float_diff_values) < target_size:
            pad_length = target_size - len(float_diff_values)
            float_diff_values = np.pad(
                float_diff_values, (0, pad_length), "constant", constant_values=0
            )
            logging.info(
                f"[{model_name}] Insufficient diff data, padded {pad_length} zeros (original {len(float_diff_values)-pad_length} → target {target_size})"
            )
        elif len(float_diff_values) > target_size:
            float_diff_values = float_diff_values[:target_size]
            logging.info(
                f"[{model_name}] Excessive diff data, truncated to {target_size} entries (original {len(float_diff_values)} → target {target_size})"
            )

        # Reshape 1D arrays into 2D matrices
        match_matrix = match_values.reshape(rows, cols)
        float_diff_matrix = float_diff_values.reshape(rows, cols)
        return match_matrix, float_diff_matrix

    def plot(self):
        """Generate heatmaps with dynamic layout matching CSV count"""
        if not self.dataframes:
            logging.info(
                "No data available for plotting, please call load_data() first"
            )
            return

        # Get number of models (equal to the number of CSV files)
        num_models = len(self.dataframes)
        if num_models == 0:
            return

        # Dynamic layout: 2 columns, auto-calculate required rows
        num_cols = 2
        num_rows = (num_models + num_cols - 1) // num_cols

        # Calculate figure size (dynamic height based on row count)
        base_width, base_height = self.config["base_figure_size"]
        fig_height = base_height * num_rows
        fig = plt.figure(figsize=(base_width, fig_height))

        # Create grid layout: 2 plot columns + 1 colorbar column
        gs = GridSpec(
            num_rows,
            3,
            figure=fig,
            width_ratios=[9, 9, 1],
            hspace=self.config["grid_hspace"],
            wspace=self.config["grid_wspace"],
        )

        # Create subplots for each model
        axes = []
        for i in range(num_models):
            row_idx = i // num_cols
            col_idx = i % num_cols
            ax = fig.add_subplot(gs[row_idx, col_idx])
            axes.append(ax)

        # Plot heatmap for each model
        im = None
        for i in range(num_models):
            ax = axes[i]
            df = self.dataframes[i]
            model_name = self.model_names[i]

            # Prepare formatted matrix data
            match_matrix, float_diff_matrix = self._prepare_matrix_data(df, model_name)

            # Plot heatmap with unified color scale
            im = ax.imshow(
                float_diff_matrix,
                cmap="coolwarm",
                aspect="auto",
                vmin=self.global_vmin,
                vmax=self.global_vmax,
            )

            # Subplot styling
            ax.set_title(model_name, pad=self.config["title_pad"])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_xlabel("")
            ax.set_ylabel("")
            # Hide plot spines and ticks
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(axis="both", which="both", length=0)

            # Draw contour lines for matching results
            rows, cols = self.config["matrix_shape"]
            for x in range(rows):
                for y in range(cols):
                    edge_color = "white" if match_matrix[x, y] == 1 else "black"
                    ax.add_patch(
                        plt.Rectangle(
                            (y - 0.5, x - 0.5),
                            1,
                            1,
                            fill=False,
                            edgecolor=edge_color,
                            linewidth=self.config["rect_linewidth"],
                        )
                    )

        # Add shared colorbar spanning all rows
        cbar_ax = fig.add_subplot(gs[:, 2])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label(self.config["colorbar_label"], rotation=270, labelpad=20)

        # Final layout adjustment and save figure
        plt.tight_layout()
        plt.savefig(
            self.config["output_filename"],
            dpi=self.config["figure_dpi"],
            bbox_inches="tight",
        )
        plt.close()
        logging.info(
            f"\nHeatmap saved to: {os.path.abspath(self.config['output_filename'])}"
        )
        logging.info(
            f"Successfully plotted {num_models} models (matching CSV files count)"
        )


if __name__ == "__main__":
    # Log the path to the output log file
    logging.info(f"Log file will be saved to: {log_file_path}")
    # Optional custom configuration
    custom_config = {
        "title_pad": 1,
        "grid_hspace": 0.1,
    }
    # Initialize plotter with CSV directory path
    plotter = CTCHeatmapPlotter(folder_path="./assembled", config=custom_config)
    if plotter.load_data():
        plotter.plot()
    else:
        logging.info("Program terminated: No CSV files found")
