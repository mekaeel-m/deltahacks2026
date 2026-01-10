"""
Quick script to collect baseline data from testing_images folder.
Run this to generate baseline_data.json from your reference images.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from baseline_collector import collect_baseline_from_folder

def main():
    # Paths
    script_dir = os.path.dirname(__file__)
    baseline_folder = os.path.join(script_dir, 'testing_images')
    output_path = os.path.join(script_dir, 'output', 'baseline_data.json')
    
    print("=" * 50)
    print("BASELINE COLLECTION")
    print("=" * 50)
    print(f"\nSource folder: {baseline_folder}")
    print(f"Output file: {output_path}")
    print()
    
    # Check if folder exists
    if not os.path.exists(baseline_folder):
        print(f"ERROR: Folder not found: {baseline_folder}")
        print("\nPlease create the folder and add baseline images.")
        return
    
    # List images
    images = [f for f in os.listdir(baseline_folder) 
              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    
    if not images:
        print(f"ERROR: No images found in {baseline_folder}")
        return
    
    print(f"Found {len(images)} images:")
    for img in images[:5]:
        print(f"  - {img}")
    if len(images) > 5:
        print(f"  ... and {len(images) - 5} more")
    print()
    
    # Collect baseline
    try:
        baseline = collect_baseline_from_folder(
            baseline_folder,
            output_path,
            aggregate_method='average'  # Use 'median' for more robust averaging
        )
        
        print("\n" + "=" * 50)
        print("BASELINE COLLECTION COMPLETE")
        print("=" * 50)
        print(f"\nImages processed: {baseline['metadata']['num_images_processed']}")
        print(f"Output saved to: {output_path}")
        
        # Show baseline summary
        print("\nBaseline Angles:")
        for arm_name, angles in baseline['baseline_angles'].items():
            print(f"\n  {arm_name}:")
            for angle_name, data in angles.items():
                if isinstance(data, dict):
                    print(f"    {angle_name}: {data['value']:.1f}° (±{data['std']:.1f}°)")
                else:
                    print(f"    {angle_name}: {data:.1f}°")
        
        print("\n✓ Baseline ready for pose comparison!")
        print("\nNext steps:")
        print("  1. Run correctForm.py to start the comparison server")
        print("  2. Send images to /compare-pose endpoint")
        print("  3. Or use /compare-pose-visual for visual feedback")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
