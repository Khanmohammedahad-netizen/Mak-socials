import argparse
import asyncio
import sys
import os
from engine.utils.logger import logger

# Add src to path just in case
# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Viral Content Engine CLI")
    parser.add_argument(
        "--run-now", action="store_true", help="Run the pipeline once immediately"
    )
    parser.add_argument(
        "--schedule", action="store_true", help="Start the 4-hour scheduler"
    )
    parser.add_argument(
        "--test", action="store_true", help="Generate script + video only, no upload"
    )
    parser.add_argument(
        "--setup", action="store_true", help="Run setup validation checks"
    )

    args = parser.parse_args()

    if args.setup:
        print("Running setup validation...")
        import setup
        setup.run_setup()
        return

    from engine.scheduler import ViralEngine, start_scheduler

    if args.run_now:
        engine = ViralEngine()
        asyncio.run(engine.run_pipeline())
    elif args.schedule:
        start_scheduler()
    elif args.test:
        engine = ViralEngine()
        # Modify config temporarily to disable platforms
        engine.config['scheduling']['platforms']['youtube'] = False
        engine.config['scheduling']['platforms']['instagram'] = False
        engine.config['scheduling']['platforms']['snapchat_email'] = False
        asyncio.run(engine.run_pipeline())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
