import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from datetime import datetime

class SessionLogger:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        
    def log(self, profile: str, window_title: str, relevance: float, kpm: float, mpm: float, focus_score: float):
        self.records.append({
            "timestamp": datetime.now(),
            "profile": profile,
            "window_title": window_title,
            "relevance": relevance,
            "kpm": kpm,
            "mpm": mpm,
            "focus_score": focus_score
        })
        
    def end_session(self) -> pd.DataFrame:
        df = pd.DataFrame(self.records)
        if not df.empty:
            filename = f"session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"Session data saved to {filename}")
        return df
        
    def plot_session(self, df: pd.DataFrame):
        if df.empty:
            print("No data to plot.")
            return
            
        plt.figure(figsize=(10, 5))
        plt.plot(df["timestamp"], df["focus_score"], label="Focus Score", color="blue", linewidth=2)
        
        # Shade background based on relevance
        # Use line segments or fill_between to accurately reflect the 5 sec intervals
        for i in range(len(df) - 1):
            rel = df.iloc[i]["relevance"]
            color = "green" if rel >= 0.5 else "red"
            alpha = max(0.1, abs(rel - 0.5) * 0.4)
            plt.axvspan(df.iloc[i]["timestamp"], df.iloc[i+1]["timestamp"], color=color, alpha=alpha, lw=0)
            
        # Detect and mark Task Switches
        task_switches = df[df["window_title"] != df["window_title"].shift(1)]
        if len(task_switches) > 1:
            task_switches = task_switches.iloc[1:] # Skip the initial open event
            plt.vlines(task_switches["timestamp"], ymin=0, ymax=100, color='purple', linestyle=':', alpha=0.6, label='Task Switch')
            plt.scatter(task_switches["timestamp"], task_switches["focus_score"], color='purple', s=30, zorder=5)
            
        plt.title("Productivity Focus Over Time")
        plt.xlabel("Time")
        plt.ylabel("Focus Score")
        plt.ylim(0, 100)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.show()
