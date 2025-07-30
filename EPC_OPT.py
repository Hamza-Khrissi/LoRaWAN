import pandas as pd
import os
from pathlib import Path
from typing import List, Dict


class EPCAnalyzer:
    def __init__(self):
        self.min_prefix_length = 6
        self.analysis_results = []
    
    def load_epcs(self, file_path: str) -> List[str]:
        """Load EPCs from file. Supports .txt, .csv, .xlsx files."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        epcs = []
        
        if path.suffix.lower() in ['.txt', '.csv']:
            # Read text/CSV files (one EPC per line)
            with open(path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    epc = line.strip()
                    if epc and len(epc) == 24 and all(c in '0123456789ABCDEFabcdef' for c in epc):
                        epcs.append(epc.upper())
                    elif epc:  # Non-empty but invalid
                        print(f"Skipping invalid EPC at line {line_num}: {epc}")
        
        elif path.suffix.lower() == '.xlsx':
            # Read Excel file (first column)
            df = pd.read_excel(path, header=None)
            for idx, epc in enumerate(df.iloc[:, 0], 1):
                epc = str(epc).strip()
                if len(epc) == 24 and all(c in '0123456789ABCDEFabcdef' for c in epc):
                    epcs.append(epc.upper())
                else:
                    print(f"Skipping invalid EPC at row {idx}: {epc}")
        
        else:
            raise ValueError("Unsupported file format. Use .txt, .csv, or .xlsx")
        
        if not epcs:
            raise ValueError("No valid EPCs found in file")
        
        print(f"Loaded {len(epcs)} valid EPCs from {path.name}")
        return epcs
    
    def group_and_analyze(self, epcs: List[str]) -> pd.DataFrame:
        """Group EPCs by prefix and analyze compression."""
        groups = []
        remaining = epcs[:]
        
        # Create groups based on common prefix
        while remaining:
            base = remaining.pop(0)
            group = [base]
            
            # Find EPCs with common prefix >= 6 chars
            i = 0
            while i < len(remaining):
                common_len = sum(1 for a, b in zip(base, remaining[i]) if a == b)
                if common_len >= self.min_prefix_length:
                    group.append(remaining.pop(i))
                else:
                    i += 1
            groups.append(group)
        
        # Analyze each group
        results = []
        for gid, group in enumerate(groups, 1):
            if len(group) == 1:
                # Single EPC - no compression
                results.append({
                    'Group_ID': gid,
                    'Prefix': '',
                    'Prefix_Bytes': 0,
                    'Suffix_Bytes': 12,
                    'Suffix_Count': 1,
                    'Total_Payload_Bytes': 14,
                    'EPCs_SF7_51B': 3,
                    'EPCs_SF12_11B': 0,
                    'Compression_%': 0
                })
            else:
                # Find common prefix
                prefix_len = min(len(min(group, key=len)), 
                               max(self.min_prefix_length,
                                   sum(1 for chars in zip(*group) if len(set(chars)) == 1)))
                
                prefix = group[0][:prefix_len]
                prefix_bytes = prefix_len // 2
                suffix_bytes = (24 - prefix_len) // 2
                suffix_count = len(group)
                
                # Calculate payload: header(1) + prefix_len(1) + prefix + suffixes
                total_payload = 2 + prefix_bytes + (suffix_count * suffix_bytes)
                
                # LoRaWAN capacity
                overhead = 2 + prefix_bytes
                epcs_sf7 = max(0, (51 - overhead) // suffix_bytes) if suffix_bytes > 0 else 0
                epcs_sf12 = max(0, (11 - overhead) // suffix_bytes) if suffix_bytes > 0 else 0
                
                # Compression ratio
                uncompressed = len(group) * 12
                compression = round(((uncompressed - total_payload) / uncompressed * 100), 1)
                
                results.append({
                    'Group_ID': gid,
                    'Prefix': prefix,
                    'Prefix_Bytes': prefix_bytes,
                    'Suffix_Bytes': suffix_bytes,
                    'Suffix_Count': suffix_count,
                    'Total_Payload_Bytes': total_payload,
                    'EPCs_SF7_51B': epcs_sf7,
                    'EPCs_SF12_11B': epcs_sf12,
                    'Compression_%': compression
                })
        
        # Store results for later use
        self.analysis_results = results
        return pd.DataFrame(results)
    
    def save_results(self, df: pd.DataFrame, output_path: str) -> str:
        """Save results to specified Excel file path."""
        try:
            # Create results DataFrame
            results_df = pd.DataFrame(self.analysis_results)
            results_df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"✅ Excel file created successfully at: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Error saving Excel file: {e}")
            return None
    
    def print_summary(self, df: pd.DataFrame):
        """Print analysis summary."""
        print("\n" + "="*80)
        print("EPC LoRaWAN Compression Analysis")
        print("="*80)
        print(df.to_string(index=False))
        
        # Statistics
        total_epcs = df['Suffix_Count'].sum()
        total_payload = df['Total_Payload_Bytes'].sum()
        uncompressed = total_epcs * 12
        savings = uncompressed - total_payload
        
        print(f"\nSummary:")
        print(f"  Total EPCs: {total_epcs} | Groups: {len(df)}")
        print(f"  Uncompressed: {uncompressed}B | Compressed: {total_payload}B")
        print(f"  Savings: {savings}B ({savings/uncompressed*100:.1f}%)")


def main():
    """
    USAGE INSTRUCTIONS:
    
    1. CREATE INPUT FILE ON DESKTOP:
       - File name: "epcs.txt" (or "epcs.csv" or "epcs.xlsx")
       - Content: One EPC per line (24 hex characters each)
    """

    INPUT_FILE = "EPCS.xlsx"
    desktop_path = "C:/Users/HamzaELKHRISSI/OneDrive - Greenerwave/Desktop/EPCS.xlsx"
    output_path = "C:/Users/HamzaELKHRISSI/OneDrive - Greenerwave/Desktop/EPCSOPT.xlsx"  # ✅ chemin de sortie

    try:
        analyzer = EPCAnalyzer()

        # Load and analyze EPCs
        epcs = analyzer.load_epcs(desktop_path)
        results_df = analyzer.group_and_analyze(epcs)

        # Display results
        analyzer.print_summary(results_df)

        # ✅ Save to Excel with output path
        excel_path = analyzer.save_results(results_df, output_path)
        print(f"\nResults saved to: {excel_path}")

    except Exception as e:
        print(f"Error: {e}")
        print(f"\nMake sure '{INPUT_FILE}' exists on your Desktop with valid EPCs!")


if __name__ == "__main__":
    main()
