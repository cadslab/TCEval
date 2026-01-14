import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec


class HeatmapPlotter:
    """Matching Result Heatmap Plotting Tool"""

    # Configuration parameters (91*91, total elements of target matrix)
    DEFAULT_CONFIG = {
        "figure_dpi": 300,
        "font_family": "Arial",
        "font_size": 12,
        "axes_titlesize": 12,
        "axes_labelsize": 12,
        "base_figure_size": (14, 4.5),  # Base size (height per row)
        "grid_hspace": 0.05,  # Modified 1: Reduce row spacing (from 0.1 to 0.05)
        "grid_wspace": 0.1,
        "colorbar_label": "PMV difference (predicted - base)",
        "output_filename": "ashrae_heatmaps.png",
        "matrix_shape": (90, 90),  # Target matrix shape (rows, columns)
        "rect_linewidth": 0.5,  # Line width of matching result contours
        "title_pad": 2,  # New config: Title padding (default 2, original default was 10)
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

        # New: Save original standard output (for later restoration)
        self.original_stdout = sys.stdout

    def _setup_matplotlib(self):
        """Configure matplotlib parameters"""
        plt.rcParams["figure.dpi"] = self.config["figure_dpi"]
        plt.rcParams["font.family"] = self.config["font_family"]
        plt.rcParams["font.size"] = self.config["font_size"]
        plt.rcParams["axes.titlesize"] = self.config["axes_titlesize"]
        plt.rcParams["axes.labelsize"] = self.config["axes_labelsize"]

    def _redirect_print_to_log(self):
        """Redirect standard output to write all print content to logs.txt (while retaining console output)"""

        # Custom file class to write to both file and console
        class DualOutput:
            def __init__(self, file_path):
                self.file = open(file_path, "w", encoding="utf-8")
                self.console = sys.stdout

            def write(self, message):
                # Write to console
                self.console.write(message)
                # Write to file
                self.file.write(message)
                # Force buffer flush to ensure real-time writing
                self.file.flush()

            def flush(self):
                self.console.flush()
                self.file.flush()

        # Redirect sys.stdout to the custom DualOutput instance
        sys.stdout = DualOutput("logs.txt")

    def _restore_stdout(self):
        """Restore original standard output and close the log file"""
        if hasattr(sys.stdout, "file"):
            sys.stdout.file.close()
        sys.stdout = self.original_stdout

    def load_data(self):
        """Load and preprocess CSV file data"""
        # Step 1: Redirect print to logs.txt (start recording global logs)
        self._redirect_print_to_log()

        # Find all CSV files
        self.csv_files = [
            os.path.join(self.folder_path, f)
            for f in os.listdir(self.folder_path)
            if f.lower().endswith(".csv")
        ]

        if not self.csv_files:
            print("No CSV files found")
            self._restore_stdout()  # Restore output in advance
            return False

        # Extract model names and load data
        self.model_names = [os.path.basename(f).split(".")[0] for f in self.csv_files]
        print(f"Found {len(self.model_names)} models: {self.model_names}")
        self.dataframes = []

        # New: Store content for report.txt (output from lines 95-108)
        report_content = []

        for idx, file in enumerate(self.csv_files):
            df = pd.read_csv(file)
            # Keep original non-null rows (mark special conditions separately later)
            # Note: Do not delete directly, but mark to avoid losing samples that need black coloring
            df = df.copy()  # Prevent modifying original data

            # MODIFICATION 1: Mark samples that meet special conditions
            # Define 4 conditions:
            # Condition 1: PMV_float < -3
            cond1 = df["PMV_float"] < -3
            # Condition 2: PMV_float > 3
            cond2 = df["PMV_float"] > 3
            # Condition 3: PMV_string is null (missing value)
            cond3 = df["PMV_string"].isna()
            # Condition 4: PMV_float is null (missing value)
            cond4 = df["PMV_float"].isna()

            # Combine all conditions (mark as black if any condition is met)
            df["is_black"] = cond1 | cond2 | cond3 | cond4

            # Original data processing: Calculate differences (valid only for non-special condition samples; special samples will be overwritten later)
            df["float_diff"] = df["PMV_float"] - df["PMV_float_base"]
            df["float_diff_abs"] = df["float_diff"].abs()
            df["string_match"] = df["PMV_string_base"] == df["PMV_string"]

            # Lines 95-108: Original print statements (capture content and write to report.txt simultaneously)
            log_lines = [
                f"[{self.model_names[idx]}] Original data rows: {len(df)}",
                f"[{self.model_names[idx]}] Matching result rows: {df['string_match'].sum()}",
                f"[{self.model_names[idx]}] Matching result ratio: {df['string_match'].sum()/len(df):.4f}",
                f"[{self.model_names[idx]}] Ratio of absolute differences < 1: {df['float_diff_abs'].lt(1).sum()/len(df):.4f}",
                f"[{self.model_names[idx]}] Black marked rows (special conditions): {df['is_black'].sum()}",
            ]

            # 1. Print to console/logs.txt (via redirection)
            for line in log_lines:
                print(line)

            # 2. Additional write to report_content (to be saved to report.txt later)
            report_content.extend(log_lines)
            report_content.append("")  # Empty line to separate different models

            self.dataframes.append(df)

        # Save report.txt (write captured content from lines 95-108)
        with open("report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(report_content))

        # Calculate global value range (exclude special marked samples to avoid affecting heatmap color scale)
        all_valid_float_diff = pd.concat(
            [df[~df["is_black"]]["float_diff"] for df in self.dataframes]
        )
        self.global_vmin = all_valid_float_diff.min()
        self.global_vmax = all_valid_float_diff.max()
        print(
            f"\nGlobal valid float_diff range: {self.global_vmin:.4f} ~ {self.global_vmax:.4f}"
        )

        return True

    def _prepare_matrix_data(self, df, model_name):
        """Prepare matrix data (ensure length matches target size, mark black positions)"""
        rows, cols = self.config["matrix_shape"]
        target_size = rows * cols

        # 1. Process string matching results (integer type)
        match_values = df["string_match"].astype(int).values
        # Pad or truncate: ensure length = target_size
        if len(match_values) < target_size:
            pad_length = target_size - len(match_values)
            match_values = np.pad(
                match_values, (0, pad_length), "constant", constant_values=0
            )
            print(
                f"[{model_name}] Insufficient matching data, padded {pad_length} zeros (original {len(match_values)-pad_length} → target {target_size})"
            )
        elif len(match_values) > target_size:
            match_values = match_values[:target_size]
            print(
                f"[{model_name}] Excessive matching data, truncated to {target_size} entries (original {len(match_values)} → target {target_size})"
            )

        # 2. Process float difference results (with black marking)
        float_diff_values = df["float_diff"].values
        # MODIFICATION 2: Get special condition marking array
        is_black_values = df["is_black"].astype(bool).values

        # First pad/truncate both the difference array and black marking array
        # Process difference array
        if len(float_diff_values) < target_size:
            pad_length = target_size - len(float_diff_values)
            float_diff_values = np.pad(
                float_diff_values, (0, pad_length), "constant", constant_values=0
            )
            # Synchronously pad black marking array (mark padded parts as False, no black coloring)
            is_black_values = np.pad(
                is_black_values, (0, pad_length), "constant", constant_values=False
            )
            print(
                f"[{model_name}] Insufficient diff data, padded {pad_length} zeros (original {len(float_diff_values)-pad_length} → target {target_size})"
            )
        elif len(float_diff_values) > target_size:
            float_diff_values = float_diff_values[:target_size]
            is_black_values = is_black_values[:target_size]
            print(
                f"[{model_name}] Excessive diff data, truncated to {target_size} entries (original {len(float_diff_values)} → target {target_size})"
            )

        # MODIFICATION 3: Set values at special condition positions to np.nan (invalid value)
        # nan will be recognized as "bad" value by matplotlib, which can be rendered as black later
        float_diff_values = np.where(is_black_values, np.nan, float_diff_values)

        # Reshape into matrix
        match_matrix = match_values.reshape(rows, cols)
        float_diff_matrix = float_diff_values.reshape(rows, cols)
        return match_matrix, float_diff_matrix

    def plot(self):
        """Generate heatmaps with dynamic layout matching CSV count"""
        if not self.dataframes:
            print("No data available for plotting, please call load_data() first")
            self._restore_stdout()  # Restore output
            return

        # Get number of models (equal to CSV files count)
        num_models = len(self.dataframes)
        if num_models == 0:
            self._restore_stdout()  # Restore output
            return

        # Calculate dynamic layout: 2 columns, auto-calculate rows
        num_cols = 2
        num_rows = (num_models + num_cols - 1) // num_cols  # Round up

        # Calculate figure size (dynamic height based on number of rows)
        base_width, base_height = self.config["base_figure_size"]
        fig_height = base_height * num_rows
        fig = plt.figure(figsize=(base_width, fig_height))

        # Create grid layout: num_rows rows, 3 columns (last column for colorbar)
        gs = GridSpec(
            num_rows,
            3,
            figure=fig,
            width_ratios=[9, 9, 1],  # 2 columns for plots, 1 for colorbar
            hspace=self.config["grid_hspace"],
            wspace=self.config["grid_wspace"],
        )

        # Dynamically create axes for each model
        axes = []
        for i in range(num_models):
            row_idx = i // num_cols
            col_idx = i % num_cols
            ax = fig.add_subplot(gs[row_idx, col_idx])
            axes.append(ax)

        # Plot each model's heatmap
        im = None  # For colorbar reference
        for i in range(num_models):
            ax = axes[i]
            df = self.dataframes[i]
            model_name = self.model_names[i]

            # Prepare matrix data
            match_matrix, float_diff_matrix = self._prepare_matrix_data(df, model_name)

            # MODIFICATION 4: Configure colormap to render nan (bad values) as black
            cmap = plt.cm.coolwarm.copy()
            cmap.set_bad(color="black")  # Key: Color invalid values as black

            # Plot heatmap (unified color range, supports nan values)
            im = ax.imshow(
                float_diff_matrix,
                cmap=cmap,
                aspect="auto",
                vmin=self.global_vmin,
                vmax=self.global_vmax,
            )

            # Subplot style
            ax.set_title(model_name, pad=self.config["title_pad"])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_xlabel("")
            ax.set_ylabel("")
            # Hide spines and ticks
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(axis="both", which="both", length=0)

            # Add matching result contours (original logic remains unchanged; black areas are not affected by contours)
            rows, cols = self.config["matrix_shape"]
            for x in range(rows):
                for y in range(cols):
                    # Skip contours for nan values (optional, to avoid visual clutter on black areas)
                    if not np.isnan(float_diff_matrix[x, y]):
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

        # Add colorbar (span all rows in last column)
        cbar_ax = fig.add_subplot(gs[:, 2])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label(self.config["colorbar_label"], rotation=270, labelpad=20)

        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(
            self.config["output_filename"],
            dpi=self.config["figure_dpi"],
            bbox_inches="tight",
        )
        plt.close()
        print(f"\nHeatmap saved to: {os.path.abspath(self.config['output_filename'])}")
        print(f"Successfully plotted {num_models} models (matching CSV files count)")

        # Final step: Restore original standard output and close log file
        self._restore_stdout()


if __name__ == "__main__":
    # Example: Customize title padding (optional)
    custom_config = {
        "title_pad": 1,  # Adjust as needed; smaller values mean tighter title spacing
        "grid_hspace": 0.1,  # Further reduce row spacing
    }
    # Example: Use current directory as CSV path
    plotter = HeatmapPlotter(folder_path="./assembled", config=custom_config)
    if plotter.load_data():
        plotter.plot()
    else:
        plotter._restore_stdout()  # Ensure output is restored even on exceptions
        print("Program terminated: No CSV files found")
