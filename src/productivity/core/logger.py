import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from datetime import datetime

class SessionLogger:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        
    def log(self, profile: str, window_title: str, relevance: float, kpm: float, mpm: float, focus_score: float, used_app_switcher: bool = False):
        self.records.append({
            "timestamp": datetime.now(),
            "profile": profile,
            "window_title": window_title,
            "relevance": relevance,
            "kpm": kpm,
            "mpm": mpm,
            "focus_score": focus_score,
            "used_app_switcher": used_app_switcher
        })
        
    def end_session(self, overlay_name: str = "default", survey_results: dict = None) -> pd.DataFrame:
        df = pd.DataFrame(self.records)
        if not df.empty:
            import os
            import json
            
            # Extract active profile safely isolating spaces natively
            profile_name = df.iloc[0]["profile"]
            safe_folder_name = "".join([c if c.isalnum() else "_" for c in profile_name]).lower()
            
            # Create isolated directory structuring seamlessly utilizing visualization
            base_dir = os.path.join("sessions", safe_folder_name, overlay_name)
            os.makedirs(base_dir, exist_ok=True)
            
            # Map secure relative filepath explicitly natively
            filepath = os.path.join(base_dir, f"session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv")
            df.to_csv(filepath, index=False)
            
            if survey_results:
                surv_path = filepath.replace(".csv", "_survey.json")
                with open(surv_path, "w") as f:
                    json.dump(survey_results, f, indent=4)
                    
            print(f"Session data saved to {filepath}")
        return df
        
    def plot_session(self, df: pd.DataFrame, survey_results: dict = None):
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
            
        if survey_results:
            textstr = '\n'.join((
                f"Productivity Feel: {survey_results.get('productivity')}/7",
                f"Distraction Level: {survey_results.get('distraction_level')}/7",
                f"Distraction Length: {survey_results.get('distraction_length')}/7",
                f"Tracking Accuracy: {survey_results.get('tracking_accuracy')}/7",
                f"Profile Adherence: {survey_results.get('profile_adherence')}/7",
                f"Mental Fatigue: {survey_results.get('mental_fatigue')}/7"
            ))
            props = dict(boxstyle='round', facecolor='white', alpha=0.7, edgecolor='gray')
            plt.gca().text(0.02, 0.95, textstr, transform=plt.gca().transAxes, fontsize=9,
                    verticalalignment='top', bbox=props, zorder=10)
            
        plt.title("Productivity Focus Over Time")
        plt.xlabel("Time")
        plt.ylabel("Focus Score")
        plt.ylim(0, 100)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.show()
