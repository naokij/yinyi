#!/usr/bin/env python3
"""
Reset all photo analysis data
- Delete all analysis records
- Clear scores and captions
- Reset status to pending

Usage:
  python reset_all_analysis.py         # Requires confirmation
  python reset_all_analysis.py --yes   # Auto confirm
"""

import sys
import argparse

sys.path.insert(0, '.')

from database import SessionLocal, Photo as PhotoModel, Analysis as AnalysisModel

def reset_all_analysis(auto_confirm=False):
    db = SessionLocal()
    try:
        # Get statistics
        total_photos = db.query(PhotoModel).count()
        analyzed_count = db.query(PhotoModel).filter(PhotoModel.status == 'analyzed').count()
        error_count = db.query(PhotoModel).filter(PhotoModel.status == 'error').count()
        pending_count = db.query(PhotoModel).filter(PhotoModel.status == 'pending').count()
        analysis_records = db.query(AnalysisModel).count()
        
        print("=" * 60)
        print("Reset Photo Analysis Data")
        print("=" * 60)
        print()
        print("Current Status:")
        print(f"  Total photos: {total_photos}")
        print(f"  Analyzed:     {analyzed_count}")
        print(f"  Error:        {error_count}")
        print(f"  Pending:      {pending_count}")
        print(f"  Analysis records: {analysis_records}")
        print()
        
        # Confirm operation
        if auto_confirm:
            print("Auto confirm mode")
        else:
            confirm = input("Reset all analysis data? This will delete all scores, captions and analysis records. (yes/no): ")
            if confirm.lower() != 'yes':
                print("Operation cancelled")
                return
        
        print()
        print("Resetting...")
        
        # 1. Delete all analysis records
        deleted_analysis = db.query(AnalysisModel).delete()
        print(f"[OK] Deleted {deleted_analysis} analysis records")
        
        # 2. Reset all photos status to pending
        updated_photos = db.query(PhotoModel).update({
            PhotoModel.status: 'pending'
        })
        print(f"[OK] Reset {updated_photos} photos to pending status")
        
        # 3. Commit changes
        db.commit()
        
        print()
        print("=" * 60)
        print("Reset Complete!")
        print("=" * 60)
        print()
        print("All photos reset to initial state:")
        print("  - Analysis records cleared")
        print("  - Scores and captions deleted")
        print("  - Status reset to pending")
        print()
        print('Click "AI Analyze All" in Web UI to start re-analysis')
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reset all photo analysis data')
    parser.add_argument('--yes', '-y', action='store_true', help='Auto confirm without interaction')
    args = parser.parse_args()
    
    reset_all_analysis(auto_confirm=args.yes)
