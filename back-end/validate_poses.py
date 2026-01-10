"""
Validation script to test poses against baseline.
Compares all images in testing_images folder against the baseline.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from baseline_collector import collect_baseline_from_folder
from pose_comparator import PoseComparator


def run_validation():
    script_dir = os.path.dirname(__file__)
    baseline_folder = os.path.join(script_dir, 'baseline_images')
    testing_folder = os.path.join(script_dir, 'testing_images')
    baseline_file = os.path.join(script_dir, 'output', 'baseline_data.json')
    
    print("=" * 60)
    print("POSE VALIDATION TEST")
    print("=" * 60)
    print(f"\nBaseline folder: {baseline_folder}")
    print(f"Testing folder: {testing_folder}")
    print()
    
    # Step 1: Collect/refresh baseline from baseline_images
    print("-" * 60)
    print("STEP 1: Collecting baseline data...")
    print("-" * 60)
    
    baseline_images = [f for f in os.listdir(baseline_folder) 
                       if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    print(f"Found {len(baseline_images)} baseline images")
    
    baseline = collect_baseline_from_folder(
        baseline_folder,
        baseline_file,
        aggregate_method='average'
    )
    print(f"✓ Baseline created from {baseline['metadata']['num_images_processed']} images\n")
    
    # Step 2: Load comparator
    print("-" * 60)
    print("STEP 2: Initializing pose comparator...")
    print("-" * 60)
    
    comparator = PoseComparator(
        baseline_path=baseline_file,
        position_threshold=0.15,  # 15% position tolerance
        angle_threshold=20.0,     # 20 degree angle tolerance
        accuracy_threshold=70.0   # 70% to be considered accurate
    )
    comparator.load_baseline()
    print("✓ Comparator ready\n")
    
    # Step 3: Test each image in testing_images
    print("-" * 60)
    print("STEP 3: Testing images...")
    print("-" * 60)
    
    test_images = [f for f in os.listdir(testing_folder) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    
    if not test_images:
        print("No test images found in testing_images folder!")
        return
    
    print(f"Found {len(test_images)} test images\n")
    
    results = []
    
    for i, filename in enumerate(sorted(test_images), 1):
        image_path = os.path.join(testing_folder, filename)
        print(f"\n[{i}/{len(test_images)}] Testing: {filename}")
        print("-" * 40)
        
        result = comparator.compare_image_file(image_path)
        flag = comparator.get_comparison_flag(result)
        
        # Ensure corrections are JSON serializable
        serializable_corrections = [
            {
                'arm': correction['arm'],
                'joint': correction['joint'],
                'message': correction['message']
            }
            for correction in flag['corrections']
        ]

        results.append({
            'filename': filename,
            'accuracy': flag['accuracy_percentage'],
            'level': flag['accuracy_level'],
            'is_accurate': flag['is_accurate'],
            'message': flag['message'],
            'corrections': serializable_corrections
        })
        
        # Print results
        status_icon = "✓" if flag['is_accurate'] else "✗"
        print(f"  {status_icon} Accuracy: {flag['accuracy_percentage']:.1f}%")
        print(f"    Level: {flag['accuracy_level'].upper()}")
        print(f"    Status: {'PASS' if flag['is_accurate'] else 'NEEDS CORRECTION'}")
        
        if flag['corrections']:
            print(f"    Corrections needed:")
            for correction in flag['corrections'][:3]:  # Show top 3
                print(f"      - {correction['arm']} {correction['joint']}: {correction['message']}")
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results if r['is_accurate'])
    failed = total - passed
    avg_accuracy = sum(r['accuracy'] for r in results) / total if total > 0 else 0
    
    print(f"\nTotal images tested: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Average accuracy: {avg_accuracy:.1f}%")
    
    print("\n" + "-" * 60)
    print("DETAILED RESULTS")
    print("-" * 60)
    print(f"{'Filename':<40} {'Accuracy':>10} {'Status':>10}")
    print("-" * 60)
    
    for r in sorted(results, key=lambda x: x['accuracy'], reverse=True):
        status = "PASS" if r['is_accurate'] else "FAIL"
        print(f"{r['filename']:<40} {r['accuracy']:>9.1f}% {status:>10}")
    
    # Ensure all objects in results are JSON serializable
    def make_serializable(obj):
        try:
            json.dumps(obj)  # Test if serializable
            return obj
        except (TypeError, ValueError):
            return str(obj)  # Fallback to string representation

    results = [
        {key: make_serializable(value) for key, value in result.items()}
        for result in results
    ]
    
    # Save results to JSON
    output_file = os.path.join(script_dir, 'output', 'validation_results.json')
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'baseline_images': baseline['metadata']['processed_files'],
            'summary': {
                'total_tested': total,
                'passed': passed,
                'failed': failed,
                'average_accuracy': avg_accuracy
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    return results


if __name__ == '__main__':
    run_validation()
