#!/usr/bin/env python3
"""
Production Test — Posts 5 tweets per persona (mix of originals + quote tweets).
Logs everything to the dashboard database.
Run: python3 prod_test.py
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
logger = logging.getLogger("prod_test")

POSTS_PER_PERSONA = 5


def main():
    from config import settings, TOPICS, SEED_ACCOUNTS
    from personas import get_personas
    from llm.router import HybridRouter
    from rag.pinecone_store import PineconeStore
    from x_api.client import XClient
    from x_api.retrieval import SeedRetriever
    from validation.content_validator import ContentValidator
    from api.database import ActivityLogger

    logger.info("=" * 60)
    logger.info(f"🇰🇪 PRODUCTION TEST — {POSTS_PER_PERSONA} posts per persona (originals + quotes)")
    logger.info("=" * 60)

    # Initialize shared services
    llm_router = HybridRouter(
        grok_api_key=settings.grok_api_key,
        claude_api_key=settings.claude_api_key,
    )

    rag_store = PineconeStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
    )

    juma_persona, amani_persona = get_personas()

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
            logger.info(f"  Stored {stored} tweets in Pinecone RAG")

            ActivityLogger.log_rag_activity(
                action="store",
                source="seed_accounts",
                query="prod_test_refresh",
                results_count=stored,
                details={"total_fetched": len(tweets)},
                persona="system"
            )
        else:
            logger.warning("  No tweets fetched from seed accounts")
    except Exception as e:
        logger.error(f"  RAG refresh failed: {e}")

    # ── Build quotable tweets pool ──
    # Pick tweets with reasonable text length for quoting
    quotable_tweets = [
        t for t in all_fetched_tweets
        if t.get("text") and len(t["text"]) > 20 and len(t["text"]) < 250
        and not t["text"].startswith("RT ")
        and t.get("id")
    ]
    random.shuffle(quotable_tweets)
    logger.info(f"  Quotable tweets pool: {len(quotable_tweets)}")

    # Initialize X clients
    juma_client = XClient(
        consumer_key=settings.kamau.consumer_key,
        consumer_secret=settings.kamau.consumer_secret,
        access_token=settings.kamau.access_token,
        access_token_secret=settings.kamau.access_token_secret,
        bearer_token=settings.kamau.bearer_token,
        persona_name="Juma",
    )

    amani_client = XClient(
        consumer_key=settings.wanjiku.consumer_key,
        consumer_secret=settings.wanjiku.consumer_secret,
        access_token=settings.wanjiku.access_token,
        access_token_secret=settings.wanjiku.access_token_secret,
        bearer_token=settings.wanjiku.bearer_token,
        persona_name="Amani",
    )

    personas = [
        (juma_persona, juma_client, "Juma"),
        (amani_persona, amani_client, "Amani"),
    ]

    # Decide random action sequence for each persona
    # ~60% original, ~40% quote tweet
    all_topic_keys = list(TOPICS.keys())
    quote_idx = 0  # Track which quotable tweet to use next

    for persona, x_client, name in personas:
        # Build random action list: True = original, False = quote
        actions = []
        for _ in range(POSTS_PER_PERSONA):
            actions.append("original" if random.random() < 0.6 else "quote")
        
        # Ensure at least 1 quote and 1 original per persona
        if "quote" not in actions:
            actions[random.randint(0, len(actions)-1)] = "quote"
        if "original" not in actions:
            actions[random.randint(0, len(actions)-1)] = "original"
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🎭 Posting for {name} ({persona.handle})")
        logger.info(f"  Action plan: {actions}")
        logger.info(f"{'='*50}")

        for post_num, action in enumerate(actions, 1):
            if action == "quote" and quote_idx < len(quotable_tweets):
                # ── QUOTE TWEET ──
                target_tweet = quotable_tweets[quote_idx]
                quote_idx += 1
                tweet_text = target_tweet["text"]
                tweet_id = str(target_tweet["id"])

                logger.info(f"\n--- Post {post_num}/{POSTS_PER_PERSONA} | 🔁 QUOTE TWEET")
                logger.info(f"  Quoting: \"{tweet_text[:80]}...\" (ID: {tweet_id})")

                # Get RAG examples for the quoted tweet's style
                examples = rag_store.retrieve_similar(tweet_text, top_k=3)
                example_texts = [e["text"] for e in examples]

                ActivityLogger.log_rag_activity(
                    action="retrieve",
                    source="pinecone",
                    query=tweet_text[:100],
                    results_count=len(examples),
                    details=examples,
                    persona=persona.handle
                )

                # Generate comment
                content, model_used, trigger_score, matched_triggers, reason = llm_router.generate(
                    topic=tweet_text,
                    persona_description=persona.get_system_prompt(),
                    rag_examples=example_texts,
                    task="quote_comment",
                    persona_type=persona.persona_type,
                )

                logger.info(f"  Model: {model_used} | Comment: {content}")

                # Log LLM routing
                ActivityLogger.log_llm_routing(
                    persona=persona.handle,
                    topic=tweet_text[:100],
                    task="quote_comment",
                    decision=model_used,
                    trigger_score=trigger_score,
                    triggers_matched=matched_triggers,
                    reason=reason
                )

                # Validate
                validator = ContentValidator()
                result = validator.validate(content, persona.handle, tweet_text[:50])
                logger.info(f"  Validation: {result.summary}")

                # Post quote tweet
                try:
                    post_result = x_client.quote_tweet(
                        quote_tweet_id=tweet_id,
                        comment=content,
                    )
                    posted_id = post_result.get("id", "unknown") if isinstance(post_result, dict) else str(post_result)
                    logger.info(f"  ✅ QUOTE POSTED! Tweet ID: {posted_id}")

                    ActivityLogger.log_post(
                        tweet_id=posted_id,
                        persona=persona.handle,
                        content=content,
                        post_type="quote_tweet",
                        llm_used=model_used,
                        quoted_tweet_id=tweet_id,
                        authenticity_score=result.authenticity_score,
                        validation_issues=result.issues + result.warnings if (result.issues or result.warnings) else None,
                    )
                except Exception as e:
                    logger.error(f"  ❌ Quote failed: {e}")
                    ActivityLogger.log_error(
                        level="ERROR", component="prod_test",
                        message=str(e), traceback=f"quote tweet_id: {tweet_id}"
                    )

            else:
                # ── ORIGINAL POST ──
                topic_key = random.choice(all_topic_keys)
                topic = random.choice(TOPICS[topic_key])

                logger.info(f"\n--- Post {post_num}/{POSTS_PER_PERSONA} | ✏️ ORIGINAL | [{topic_key}] {topic[:60]}...")

                examples = rag_store.retrieve_similar(topic, top_k=5)
                example_texts = [e["text"] for e in examples]
                logger.info(f"  RAG examples: {len(example_texts)}")

                ActivityLogger.log_rag_activity(
                    action="retrieve",
                    source="pinecone",
                    query=topic,
                    results_count=len(examples),
                    details=examples,
                    persona=persona.handle
                )

                content, model_used, trigger_score, matched_triggers, reason = llm_router.generate(
                    topic=topic,
                    persona_description=persona.get_system_prompt(),
                    rag_examples=example_texts,
                    task="original_post",
                    persona_type=persona.persona_type,
                )

                logger.info(f"  Model: {model_used} | Triggers: {trigger_score}")
                logger.info(f"  Generated: {content}")

                ActivityLogger.log_llm_routing(
                    persona=persona.handle,
                    topic=topic,
                    task="original_post",
                    decision=model_used,
                    trigger_score=trigger_score,
                    triggers_matched=matched_triggers,
                    reason=reason
                )

                validator = ContentValidator()
                result = validator.validate(content, persona.handle, topic)
                logger.info(f"  Validation: {result.summary}")

                try:
                    post_result = x_client.post_tweet(content)
                    posted_id = post_result.get("id", "unknown") if isinstance(post_result, dict) else str(post_result)
                    logger.info(f"  ✅ POSTED! Tweet ID: {posted_id}")

                    ActivityLogger.log_post(
                        tweet_id=posted_id,
                        persona=persona.handle,
                        content=content,
                        post_type="original_post",
                        llm_used=model_used,
                        authenticity_score=result.authenticity_score,
                        validation_issues=result.issues + result.warnings if (result.issues or result.warnings) else None,
                    )
                except Exception as e:
                    logger.error(f"  ❌ Post failed: {e}")
                    ActivityLogger.log_error(
                        level="ERROR", component="prod_test",
                        message=str(e), traceback=f"topic: {topic}, persona: {persona.handle}"
                    )

            # Small delay between posts to be nice to the API
            time.sleep(2)

    logger.info("\n" + "=" * 60)
    logger.info("🏁 Production test complete! Check X accounts and dashboard.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
