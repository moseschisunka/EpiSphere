"""
Background task script for running automated outbreak detection
Can be run as a cron job or scheduled task
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.outbreak_detection_service import OutbreakDetectionService


def main():
    """Run outbreak detection for all countries and diseases"""
    print("Starting outbreak detection scan...")
    
    db = SessionLocal()
    try:
        service = OutbreakDetectionService(db)
        results = service.run_detection_for_all_countries()
        
        print(f"\nDetection complete. Found {len(results)} alerts.")
        
        for result in results:
            print(f"\nAlert triggered:")
            print(f"  Country: {result.get('country_name', 'Unknown')}")
            print(f"  Disease: {result.get('disease_name', 'Unknown')}")
            print(f"  Severity: {result.get('severity', 'Unknown')}")
            print(f"  Probability: {result.get('probability_score', 0) * 100:.1f}%")
            print(f"  Method: {result.get('detection_method', 'Unknown')}")
    
    except Exception as e:
        print(f"Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
