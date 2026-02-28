#!/usr/bin/env python3
"""
Dry Run — Generates 2 posts per persona using the LLM.
NO actual tweets are posted to X.
All activity is logged to the dashboard database so you can see it live.

Run: python3 dry_run.py
"""

import logging
import sys
import random
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dry_run")

POSTS_PER_PERSONA = 2
DRY_RUN_TWEET_ID = "DRY_RUN_NO_POST"


def main():
    from config import settings, TOPICS, SEED_ACCOUNTS, PERSONA_TOPICS
    from personas import get_personas
    from llm.router import HybridRouter
    from rag.pinecone_store import PineconeStore
    from x_api.retrieval import SeedRetriever
    from validation.content_validator import ContentValidator
    from api.database import ActivityLogger

    logger.info("=" * 60)
    logger.info("🌍 NAIROBI SWAHILI BOT — DRY RUN (NO X POSTING)")
    logger.info(f"   {POSTS_PER_PERSONA} posts per persona | All 7 personas included")
    logger.info("   ✅ LLM generation ON | ❌ X posting OFF | 📊 Dashboard logging ON")
    logger.info("=" * 60)

    # ── Initialize shared services ──
    logger.info("\n⚙️  Initializing LLM router...")
    llm_router = HybridRouter(
        grok_api_key=settings.grok_api_key,
        claude_api_key=settings.claude_api_key,
    )

    logger.info("⚙️  Connecting to Pinecone RAG store...")
    rag_store = PineconeStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
    )

    all_personas = get_personas()
    logger.info(f"\n✅ Loaded {len(all_personas)} personas:")
    for p in all_personas:
        logger.info(f"   - {p.name} ({p.handle}) [{p.persona_type}]")

    # ── Refresh RAG from seed accounts ──
    logger.info("\n📡 Refreshing RAG from seed accounts...")
    retriever = SeedRetriever(bearer_token=settings.kamau.bearer_token)
    all_fetched_tweets = []

    try:
        tweets = retriever.fetch_from_seed_accounts(
            seed_accounts=SEED_ACCOUNTS,
            max_per_account=20,
        )
        if tweets:
            all_fetched_tweets = tweets
            stored = rag_store.store_tweets(tweets, source_account="seed_mix")
            logger.info(f"  ✅ Stored {stored} tweets in Pinecone RAG")
            ActivityLogger.log_rag_activity(
                action="store", source="seed_accounts",
                query="dry_run_refresh", results_count=stored,
                details={"total_fetched": len(tweets)}, persona="system"
            )
        else:
            logger.warning("  ⚠️  No tweets fetched — RAG will use existing index")
    except Exception as e:
        logger.error(f"  ❌ RAG refresh failed: {e}")
        logger.info("  Continuing with existing RAG index...")

    # ── Build quotable tweets pool ──
    quotable_tweets = [
        t for t in all_fetched_tweets
        if t.get("text") and len(t["text"]) > 20 and len(t["text"]) < 250
        and not t["text"].startswith("RT ")
        and t.get("id")
    ]
    random.shuffle(quotable_tweets)
    logger.info(f"  Quotable tweets pool: {len(quotable_tweets)}")

    all_topic_keys = list(TOPICS.keys())
    quote_idx = 0

    # ── Run all 7 personas (dry run bypasses credential check) ──
    logger.info(f"\n🎭 Starting dry run for all {len(all_personas)} personas...")

    for persona in all_personas:
        # Build action list: mix of original + quote
        actions = []
        for _ in range(POSTS_PER_PERSONA):
            actions.append("original" if random.random() < 0.6 else "quote")
        # Ensure at least one original in a small run
        if "original" not in actions:
            actions[0] = "original"

        logger.info(f"\n{'='*60}")
        logger.info(f"🎭 DRY RUN — {persona.name} ({persona.handle})")
        logger.info(f"   Type: {persona.persona_type} | Actions: {actions}")
        logger.info(f"{'='*60}")

        for post_num, action in enumerate(actions, 1):
            use_quote = action == "quote" and quote_idx < len(quotable_tweets)

            if use_quote:
                # ── QUOTE TWEET (dry run) ──
                target_tweet = quotable_tweets[quote_idx]
                quote_idx += 1
                tweet_text = target_tweet["text"]
                tweet_id = str(target_tweet["id"])

                logger.info(f"\n--- Post {post_num}/{POSTS_PER_PERSONA} | 🔁 QUOTE TWEET (DRY RUN)")
                logger.info(f"  Would quote: \"{tweet_text[:80]}...\" (ID: {tweet_id})")

                try:
                    examples = rag_store.retrieve_similar(tweet_text, top_k=3)
                    example_texts = [e["text"] for e in examples]
                except Exception as e:
                    logger.warning(f"  RAG retrieve failed: {e}")
                    example_texts = []

                ActivityLogger.log_rag_activity(
                    action="retrieve", source="pinecone",
                    query=tweet_text[:100], results_count=len(example_texts),
                    details=[], persona=persona.handle
                )

                try:
                    content, model_used, trigger_score, matched_triggers, reason = llm_router.generate(
                        topic=tweet_text,
                        persona_description=persona.get_system_prompt(),
                        rag_examples=example_texts,
                        task="quote_comment",
                        persona_type=persona.persona_type,
                    )
                except Exception as e:
                    logger.error(f"  ❌ LLM generation failed: {e}")
                    ActivityLogger.log_error(
                        level="ERROR", component="dry_run",
                        message=f"LLM failed for {persona.handle}: {e}",
                        traceback=f"task=quote_comment persona={persona.handle}"
                    )
                    time.sleep(2)
                    continue

                logger.info(f"  Model: {model_used} (trigger score: {trigger_score})")
                logger.info(f"  📝 Generated comment: {content}")

                ActivityLogger.log_llm_routing(
                    persona=persona.handle, topic=tweet_text[:100],
                    task="quote_comment", decision=model_used,
                    trigger_score=trigger_score,
                    triggers_matched=matched_triggers, reason=reason
                )

                validator = ContentValidator()
                result = validator.validate(content, persona.handle, tweet_text[:50])
                logger.info(f"  Validation: {result.summary}")
                logger.info(f"  ⏭️  [DRY RUN] Skipping actual X post")

                # Log as a dry run post to dashboard
                ActivityLogger.log_post(
                    tweet_id=f"{DRY_RUN_TWEET_ID}_{persona.handle}_{post_num}",
                    persona=persona.handle,
                    content=f"[DRY RUN] {content}",
                    post_type="quote_tweet",
                    llm_used=model_used,
                    quoted_tweet_id=tweet_id,
                    authenticity_score=result.authenticity_score,
                    validation_issues=(result.issues + result.warnings)
                        if (result.issues or result.warnings) else None,
                )
                logger.info(f"  ✅ Logged to dashboard DB (dry run)")

            else:
                # ── ORIGINAL POST (dry run) ──
                persona_topic_keys = PERSONA_TOPICS.get(persona.credentials_key, all_topic_keys)
                topic_key = random.choice(persona_topic_keys)
                topic = random.choice(TOPICS[topic_key])

                logger.info(f"\n--- Post {post_num}/{POSTS_PER_PERSONA} | ✏️ ORIGINAL (DRY RUN)")
                logger.info(f"  Topic [{topic_key}]: {topic[:70]}")

                try:
                    examples = rag_store.retrieve_similar(topic, top_k=5)
                    example_texts = [e["text"] for e in examples]
                    logger.info(f"  RAG examples found: {len(example_texts)}")
                except Exception as e:
                    logger.warning(f"  RAG retrieve failed: {e}")
                    example_texts = []

                ActivityLogger.log_rag_activity(
                    action="retrieve", source="pinecone",
                    query=topic, results_count=len(example_texts),
                    details=[], persona=persona.handle
                )

                try:
                    content, model_used, trigger_score, matched_triggers, reason = llm_router.generate(
                        topic=topic,
                        persona_description=persona.get_system_prompt(),
                        rag_examples=example_texts,
                        task="original_post",
                        persona_type=persona.persona_type,
                    )
                except Exception as e:
                    logger.error(f"  ❌ LLM generation failed: {e}")
                    ActivityLogger.log_error(
                        level="ERROR", component="dry_run",
                        message=f"LLM failed for {persona.handle}: {e}",
                        traceback=f"task=original_post topic={topic} persona={persona.handle}"
                    )
                    time.sleep(2)
                    continue

                logger.info(f"  Model: {model_used} (trigger score: {trigger_score})")
                logger.info(f"  📝 Generated tweet:\n     {content}")

                ActivityLogger.log_llm_routing(
                    persona=persona.handle, topic=topic, task="original_post",
                    decision=model_used, trigger_score=trigger_score,
                    triggers_matched=matched_triggers, reason=reason
                )

                validator = ContentValidator()
                result = validator.validate(content, persona.handle, topic)
                logger.info(f"  Validation: {result.summary}")
                logger.info(f"  ⏭️  [DRY RUN] Skipping actual X post")

                # Log as a dry run post to dashboard
                ActivityLogger.log_post(
                    tweet_id=f"{DRY_RUN_TWEET_ID}_{persona.handle}_{post_num}",
                    persona=persona.handle,
                    content=f"[DRY RUN] {content}",
                    post_type="original_post",
                    llm_used=model_used,
                    authenticity_score=result.authenticity_score,
                    validation_issues=(result.issues + result.warnings)
                        if (result.issues or result.warnings) else None,
                )
                logger.info(f"  ✅ Logged to dashboard DB (dry run)")

            time.sleep(2)

        logger.info(f"\n✅ {persona.name} — {POSTS_PER_PERSONA} posts generated (dry run)")

    logger.info("\n" + "=" * 60)
    logger.info("🏁 DRY RUN COMPLETE!")
    logger.info(f"   {len(all_personas)} personas × {POSTS_PER_PERSONA} posts = {len(all_personas) * POSTS_PER_PERSONA} total generations")
    logger.info("   No tweets were posted to X.")
    logger.info("   Check your dashboard to see all logged activity! 📊")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
