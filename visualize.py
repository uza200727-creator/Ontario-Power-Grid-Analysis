import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt

from scraper.fetch_ieso import fetch_grid_data


ROOT = Path(__file__).resolve().parent


def load_module(module_name: str, file_name: str):
    file_path = ROOT / file_name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plot_generation_mix(output_path: Path) -> Path:
    df = fetch_grid_data()
    if df is None or df.empty:
        raise RuntimeError("Could not fetch current grid data for generation mix chart.")

    mix = (
        df.groupby("Fuel", as_index=False)["Output_MW"]
        .sum()
        .sort_values("Output_MW", ascending=False)
    )

    plt.figure(figsize=(9, 5))
    plt.bar(mix["Fuel"], mix["Output_MW"], color="#3b82f6")
    plt.title("Ontario Current Generation Mix by Fuel")
    plt.xlabel("Fuel Type")
    plt.ylabel("Output (MW)")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def plot_then_vs_now(output_path: Path) -> Path:
    audit_module = load_module("audit_history", "audit-history.py")
    last_night_module = load_module("last_night_gas_gen", "last-night-gas-gen.py")

    feb_2021_avg = audit_module.run_2021_audit()
    _, _, last_7_avg, _ = last_night_module.average_gas_at_hour_last_n_nights(
        n_nights=7,
        target_hour=2,
    )

    if feb_2021_avg is None or last_7_avg is None:
        raise RuntimeError("Could not calculate one or both comparison values.")

    labels = ["Feb 2021 Avg (2 AM)", "Last 7 Nights Avg (2 AM)"]
    values = [feb_2021_avg, last_7_avg]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=["#64748b", "#f97316"])
    plt.title("Ontario Gas Output Comparison at 2 AM")
    plt.ylabel("Gas Output (MW)")

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,.0f} MW",
            ha="center",
            va="bottom",
        )

    diff = last_7_avg - feb_2021_avg
    pct = (diff / feb_2021_avg) * 100 if feb_2021_avg else 0
    plt.figtext(0.5, 0.01, f"Increase: {diff:,.0f} MW ({pct:.1f}%)", ha="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def main():
    mix_path = plot_generation_mix(ROOT / "generation_mix.png")
    print(f"Saved: {mix_path}")

    compare_path = plot_then_vs_now(ROOT / "gas_then_vs_now.png")
    print(f"Saved: {compare_path}")


if __name__ == "__main__":
    main()
