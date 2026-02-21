#!/usr/bin/env python3
"""
Nairobi Swahili Bot - Main Entry Point
Autonomous X persona bots with hybrid LLM routing and cloud-based RAG.
"""

import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("nairobi_bot.log"),
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    from config import settings
    from scheduler.loop import MVPLoop
    
    logger.info("=" * 60)
    logger.info("🇰🇪 NAIROBI SWAHILI BOT - X PERSONA BOTS")
    logger.info("=" * 60)
    logger.info(f"Personas: Juma (@kamaukeeeraw), Amani (@wanjikusagee)")
    logger.info(f"Loop interval: {settings.loop_interval_hours} hours")
    logger.info(f"Dry run mode: {settings.dry_run}")
    logger.info("=" * 60)
    
    # Print start confirmations
    from personas import get_personas
    
    juma, amani = get_personas()
    
    logger.info(f"Juma: {juma.get_start_confirmation()}")
    logger.info(f"Amani: {amani.get_start_confirmation()}")
    logger.info("=" * 60)
    
    # Initialize and start loop
    logger.info("Initializing MVP Loop...")
    loop = MVPLoop(dry_run=settings.dry_run)
    
    # Start loop (this blocks)
    loop.start(
        interval_hours=settings.loop_interval_hours,
        start_time_est=settings.start_time_est
    )


if __name__ == "__main__":
    main()
