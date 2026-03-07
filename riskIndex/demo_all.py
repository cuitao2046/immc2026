#!/usr/bin/env python3
"""
Complete Demo: Run all phases of the Protected Area Risk Model
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def main():
    """Run all phase demos."""
    print_header("PROTECTED AREA RISK INDEX MODEL - COMPLETE DEMO")
    print("\nThis script runs all 6 phases of the model implementation.")
    print("="*70)

    # Import and run Phase 1
    print_header("PHASE 1: Core Model Implementation")
    import demo_phase1
    demo_phase1.main()

    # Import and run Phase 2
    print_header("PHASE 2: Risk Integration & Normalization")
    import demo_phase2
    demo_phase2.main()

    # Import and run Phase 3
    print_header("PHASE 3: Data Generation & Input/Output")
    import demo_phase3
    demo_phase3.main()

    # Import and run Phase 4
    print_header("PHASE 4: Visualization")
    import demo_phase4
    demo_phase4.main()

    # Import and run Phase 5
    print_header("PHASE 5: Testing & Validation")
    import demo_phase5
    demo_phase5.main()

    # Import and run Phase 6
    print_header("PHASE 6: Advanced Features (IMMC Enhancements)")
    import demo_phase6
    demo_phase6.main()

    print_header("✓ ALL PHASES COMPLETE!")
    print("\n" + "="*70)
    print("  Protected Area Risk Index Model - Full Implementation Complete")
    print("="*70)
    print("\nSummary:")
    print("  ✓ Phase 1: Core data structures and risk calculators")
    print("  ✓ Phase 2: Composite risk and normalization")
    print("  ✓ Phase 3: Synthetic data generation and I/O")
    print("  ✓ Phase 4: Visualization (heatmaps, analysis plots)")
    print("  ✓ Phase 5: Testing and validation")
    print("  ✓ Phase 6: IMMC enhancements (Spatio-Temporal Risk Field, DSSA)")
    print("\n" + "="*70)
    print("\nNext steps:")
    print("  - View the generated plots in the 'plots/' directory")
    print("  - Check the documentation in 'RISK_MODEL_DESIGN.md'")
    print("  - Review the code in 'src/risk_model/'")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
