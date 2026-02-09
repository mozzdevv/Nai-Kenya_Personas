#!/usr/bin/env python3
"""
Kikuyu Project - Main Entry Point
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
        logging.FileHandler("kikuyu_bot.log"),
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    from config import settings
    from scheduler.loop import MVPLoop
    
    logger.info("=" * 60)
    logger.info("🇰🇪 KIKUYU PROJECT - X PERSONA BOTS")
    logger.info("=" * 60)
    logger.info(f"Personas: Kamau (@KamauRawKE), Wanjiku (@WanjikuSage)")
    logger.info(f"Loop interval: {settings.loop_interval_hours} hours")
    logger.info(f"Dry run mode: {settings.dry_run}")
    logger.info("=" * 60)
    
    # Print start confirmations
    from personas.base import KamauPersona, WanjikuPersona
    
    kamau = KamauPersona(
        name="", handle="", description="", tone="sarcastic",
        personality_traits=[], topics=[], signature_phrases=[],
        proverb_style="", persona_type="edgy"
    )
    wanjiku = WanjikuPersona(
        name="", handle="", description="", tone="wise",
        personality_traits=[], topics=[], signature_phrases=[],
        proverb_style="", persona_type="nurturing"
    )
    
    logger.info(f"Kamau: {kamau.get_start_confirmation()}")
    logger.info(f"Wanjiku: {wanjiku.get_start_confirmation()}")
    logger.info("=" * 60)
    
    # Initialize and start loop
    loop = MVPLoop(dry_run=settings.dry_run)
    loop.start(interval_hours=settings.loop_interval_hours)


if __name__ == "__main__":
    main()
