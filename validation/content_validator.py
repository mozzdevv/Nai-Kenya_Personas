"""
Content Authenticity Validator
Validates generated tweets for authenticity before posting.
Three-layer validation: anti-pattern filter, style scoring, contextual grounding.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Nairobi timezone
EAT = timezone(timedelta(hours=3))

# ─── Constants ───────────────────────────────────────────────────────

# Well-known Kenyan hashtags (allow these)
APPROVED_HASHTAGS = {
    "#kot", "#kenyantwitter", "#nairobi", "#kenya", "#254",
    "#genzkenyans", "#kenyansontwitter", "#eastafrica",
    "#rutomustgo", "#kenyakwanza", "#azimio", "#maandamano",
    "#hustlerfund", "#nairobicity", "#madeinkenya",
}

# English framers that real locals never use
AI_ENGLISH_FRAMERS = [
    "our ancestors knew",
    "as our elders say",
    "as they say in kikuyu",
    "in kikuyu culture",
    "in our tradition",
    "which translates to",
    "which means",
    "this proverb means",
    "the wisdom here is",
    "the lesson is",
]

# Formal connectors that sound robotic
FORMAL_CONNECTORS = [
    "furthermore", "additionally", "moreover", "in conclusion",
    "therefore", "consequently", "nevertheless", "subsequently",
    "in summary", "to summarize", "as a result", "it is important to",
    "it should be noted", "one might say",
]

# Morning-specific words
MORNING_WORDS = ["asubuhi", "morning", "dawn", "sunrise"]
EVENING_WORDS = ["jioni", "evening", "sunset", "night"]

# Swahili/Sheng words (common, for code-switch ratio detection)
SWAHILI_SHENG_MARKERS = {
    "sasa", "maze", "bana", "aki", "nkt", "lakini", "kama", "sana",
    "tu", "ata", "hii", "yetu", "watu", "ni", "ya", "na", "wa",
    "kwa", "ile", "hapa", "saa", "leo", "jana", "kesho", "kweli",
    "pesa", "kazi", "bei", "ndio", "hapana", "bado", "sawa",
    "matatu", "fare", "rent", "hustle", "biashara", "serikali",
    "unaona", "unajua", "tunaishi", "wueh", "eh", "si", "ama",
    "mtu", "watu", "jamaa", "dame", "msee", "buda", "mathee",
    "mbogi", "dem", "dishi", "fiti", "poa", "noma", "rada",
    "cheki", "soma", "ambia", "peleka", "chunga", "angalia",
}

# Kikuyu markers
KIKUYU_MARKERS = {
    "gĩkũyũ", "mũciĩ", "nyũmba", "thĩĩ", "ũtheri", "mũndũ",
    "kĩugo", "thimo", "mũgĩthi", "gũtirĩ", "kĩega", "mũgo",
    "rĩĩtwa", "kĩrĩra", "ĩno", "ngai", "mwene", "nyaga",
    "cucu", "guka", "mũtumia", "mũndũ", "nĩ", "gũkũ",
    "rũciũ", "mũtĩ", "nyeki", "kĩondo", "mũgunda",
}


@dataclass
class ValidationResult:
    """Result of content validation."""
    passed: bool
    authenticity_score: int  # 0-100
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        """Human-readable summary."""
        status = "PASS" if self.passed else "FAIL"
        parts = [f"{status} (score: {self.authenticity_score})"]
        if self.issues:
            parts.append(f"Issues: {'; '.join(self.issues)}")
        if self.warnings:
            parts.append(f"Warnings: {'; '.join(self.warnings)}")
        return " | ".join(parts)


class ContentValidator:
    """
    Validates generated tweets for authenticity.
    
    Usage:
        validator = ContentValidator()
        result = validator.validate(content, persona_handle, topic)
        if not result.passed:
            # regenerate content
    """
    
    def __init__(self, recent_posts: Optional[List[str]] = None):
        """
        Args:
            recent_posts: Last 5-10 posts from this persona (for repetition check)
        """
        self.recent_posts = recent_posts or []
    
    def validate(
        self,
        content: str,
        persona_handle: str,
        topic: str,
    ) -> ValidationResult:
        """
        Run all validation layers on generated content.
        
        Args:
            content: Generated tweet text
            persona_handle: e.g. "@kamaukeeeraw"
            topic: Topic the content was generated for
            
        Returns:
            ValidationResult with pass/fail, score, and issues
        """
        issues = []
        warnings = []
        score = 100  # Start at 100, deduct for problems
        
        # ── Layer 1: Anti-Pattern Filter ──
        ap_issues, ap_warnings, ap_deductions = self._check_anti_patterns(content)
        issues.extend(ap_issues)
        warnings.extend(ap_warnings)
        score -= ap_deductions
        
        # ── Layer 2: Style Authenticity ──
        style_warnings, style_deductions = self._check_style_authenticity(content)
        warnings.extend(style_warnings)
        score -= style_deductions
        
        # ── Layer 3: Contextual Fit ──
        ctx_warnings, ctx_deductions = self._check_contextual_fit(content)
        warnings.extend(ctx_warnings)
        score -= ctx_deductions
        
        # Clamp score
        score = max(0, min(100, score))
        
        # Pass threshold: score >= 50 AND no hard failures
        passed = score >= 50 and len(issues) == 0
        
        result = ValidationResult(
            passed=passed,
            authenticity_score=score,
            issues=issues,
            warnings=warnings,
        )
        
        logger.info(f"[{persona_handle}] Validation: {result.summary}")
        return result
    
    # ── Layer 1: Anti-Pattern Filter ─────────────────────────────────
    
    def _check_anti_patterns(self, content: str) -> Tuple[List[str], List[str], int]:
        """
        Check for AI-detection red flags.
        
        Returns:
            (hard_issues, warnings, total_score_deduction)
        """
        issues = []
        warnings = []
        deductions = 0
        content_lower = content.lower()
        
        # 1. Over-length
        if len(content) > 280:
            issues.append(f"Over 280 chars ({len(content)})")
            deductions += 30
        
        # 2. Repetitive opener (check against recent posts)
        if self.recent_posts:
            first_words = content.split()[:3]
            opener = " ".join(first_words).lower() if first_words else ""
            for prev in self.recent_posts[-5:]:
                prev_opener = " ".join(prev.split()[:3]).lower()
                if opener and prev_opener and opener == prev_opener:
                    issues.append(f"Repetitive opener: '{opener}'")
                    deductions += 25
                    break
        
        # 3. English translations of proverbs
        for framer in AI_ENGLISH_FRAMERS:
            if framer in content_lower:
                issues.append(f"English proverb framer: '{framer}'")
                deductions += 20
                break
        
        # 4. Formal connectors
        for connector in FORMAL_CONNECTORS:
            if connector in content_lower:
                issues.append(f"Formal connector: '{connector}'")
                deductions += 15
                break
        
        # 5. Invented hashtags
        hashtags = re.findall(r'#\w+', content_lower)
        for tag in hashtags:
            if tag not in APPROVED_HASHTAGS:
                warnings.append(f"Unapproved hashtag: {tag}")
                deductions += 5
        
        # 6. Exclamation/emoji stacking
        excl_count = content.count("!")
        if excl_count >= 3:
            warnings.append(f"Exclamation stacking ({excl_count}x)")
            deductions += 10
        
        emoji_count = len(re.findall(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002702-\U000027B0\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]',
            content
        ))
        if emoji_count >= 3:
            warnings.append(f"Emoji overload ({emoji_count} emojis)")
            deductions += 8
        
        # 7. Over-structured (3+ complete sentences ending in period)
        sentences = [s.strip() for s in re.split(r'[.!?]', content) if s.strip()]
        if len(sentences) >= 4:
            warnings.append(f"Over-structured ({len(sentences)} sentences)")
            deductions += 10
        
        # 8. URL-like placeholders
        if "https://t.co/xyz" in content_lower or "https://t.co/" in content_lower:
            warnings.append("Contains placeholder URL")
            deductions += 5
            
        return issues, warnings, deductions
    
    # ── Layer 2: Style Authenticity ──────────────────────────────────
    
    def _check_style_authenticity(self, content: str) -> Tuple[List[str], int]:
        """
        Score the tweet's stylistic authenticity against real Nairobi Twitter patterns.
        
        Returns:
            (warnings, score_deduction)
        """
        warnings = []
        deductions = 0
        
        words = content.lower().split()
        total_words = len(words)
        
        if total_words == 0:
            return ["Empty content"], 50
        
        # ── Code-switching ratio ──
        swahili_sheng_count = sum(1 for w in words if w.strip(".,!?;:\"'()") in SWAHILI_SHENG_MARKERS)
        kikuyu_count = sum(1 for w in words if w.strip(".,!?;:\"'") in KIKUYU_MARKERS)
        local_ratio = (swahili_sheng_count + kikuyu_count) / total_words
        
        if local_ratio < 0.15:
            warnings.append(f"Too much English ({(1-local_ratio)*100:.0f}% English)")
            deductions += 12
        elif local_ratio > 0.85:
            warnings.append(f"Almost no English ({local_ratio*100:.0f}% local)")
            deductions += 5
        
        # ── Average word length (real tweets = shorter words) ──
        avg_word_len = sum(len(w) for w in words) / total_words
        if avg_word_len > 7:
            warnings.append(f"Words too long (avg {avg_word_len:.1f} chars) — real tweets use shorter words")
            deductions += 8
        
        # ── Punctuation density (real tweets = sparse) ──
        punct_count = sum(1 for c in content if c in ".,;:!?")
        punct_ratio = punct_count / len(content) if content else 0
        if punct_ratio > 0.06:
            warnings.append(f"Heavy punctuation ({punct_ratio*100:.1f}%)")
            deductions += 5
        
        # ── Capital letter ratio (real tweets are mostly lowercase) ──
        alpha_chars = [c for c in content if c.isalpha()]
        if alpha_chars:
            upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if upper_ratio > 0.25:
                warnings.append(f"Too many capitals ({upper_ratio*100:.0f}%)")
                deductions += 5
        
        return warnings, deductions
    
    # ── Layer 3: Contextual Fit ──────────────────────────────────────
    
    def _check_contextual_fit(self, content: str) -> Tuple[List[str], int]:
        """
        Check time-of-day and contextual appropriateness.
        
        Returns:
            (warnings, score_deduction)
        """
        warnings = []
        deductions = 0
        content_lower = content.lower()
        
        now = datetime.now(EAT)
        hour = now.hour
        
        # Morning content at night
        if hour >= 20 or hour < 5:
            for word in MORNING_WORDS:
                if word in content_lower:
                    warnings.append(f"Morning reference ('{word}') at nighttime")
                    deductions += 8
                    break
        
        # Evening content in the morning
        if 5 <= hour < 12:
            for word in EVENING_WORDS:
                if word in content_lower:
                    warnings.append(f"Evening reference ('{word}') in the morning")
                    deductions += 8
                    break
        
        return warnings, deductions
    
    # ── Utility: Strip problematic content ───────────────────────────
    
    @staticmethod
    def strip_unapproved_hashtags(content: str) -> str:
        """Remove hashtags that aren't in the approved list."""
        def replace_hashtag(match):
            tag = match.group(0).lower()
            return match.group(0) if tag in APPROVED_HASHTAGS else ""
        
        cleaned = re.sub(r'#\w+', replace_hashtag, content)
        # Clean up double spaces
        cleaned = re.sub(r'  +', ' ', cleaned).strip()
        return cleaned
