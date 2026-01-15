"""
Venue Newsletter Generator - Prototype
Demonstrates the core workflow for generating wedding venue newsletters
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.brand_guidelines import BRAND_GUIDELINES, BRAND_VOICE, NEWSLETTER_GUIDELINES


class NewsletterGenerator:
    """Main class for generating venue newsletters"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize with API keys"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.brand_guidelines = BRAND_GUIDELINES
        self.brand_voice = BRAND_VOICE

    def suggest_topics(self, section_type: str, num_suggestions: int = 5) -> List[Dict]:
        """
        Phase 1: Generate topic suggestions for a newsletter section

        Args:
            section_type: 'news', 'tip', or 'trend'
            num_suggestions: Number of topic options to generate

        Returns:
            List of topic suggestions with title, description, keywords
        """
        print(f"\n[*] Researching {section_type} topics...")

        # In real implementation, this would:
        # 1. Search the web for trending wedding industry topics
        # 2. Use AI to analyze and curate topics
        # 3. Format according to section type

        # PROTOTYPE: Return mock suggestions
        mock_suggestions = {
            "news": [
                {
                    "id": 1,
                    "title": "Branded Weddings Take the Spotlight",
                    "description": "61% of couples now open to brand sponsorships at weddings",
                    "keywords": ["sponsorship", "brands", "revenue", "Gen Z"],
                    "source_url": "https://nypost.com/2024/10/13/lifestyle/shocking-number-of-americans-open-to-having-their-wedding-sponsored/"
                },
                {
                    "id": 2,
                    "title": "Micro-Weddings See 40% Increase in 2025",
                    "description": "Intimate celebrations becoming the new normal for budget-conscious couples",
                    "keywords": ["micro-weddings", "intimate", "budget", "trends"],
                    "source_url": "https://example.com/micro-weddings-2025"
                },
                {
                    "id": 3,
                    "title": "Sustainable Venues Command Premium Pricing",
                    "description": "Eco-friendly venues charging 25% more as couples prioritize sustainability",
                    "keywords": ["sustainability", "eco-friendly", "pricing", "premium"],
                    "source_url": "https://example.com/sustainable-venues"
                }
            ],
            "tip": [
                {
                    "id": 1,
                    "title": "Hyper-Personalize the Client Experience",
                    "description": "Make every wedding feel uniquely crafted to the individual client",
                    "keywords": ["personalization", "client experience", "CRM", "data"],
                    "source_url": "https://www.theglobeandmail.com/life/article-hyper-personalized-weddings/"
                },
                {
                    "id": 2,
                    "title": "Leverage Video Tours to Boost Bookings",
                    "description": "How virtual venue tours increase conversion rates by 60%",
                    "keywords": ["video", "virtual tours", "bookings", "technology"],
                    "source_url": "https://example.com/video-tours"
                },
                {
                    "id": 3,
                    "title": "Master Seasonal Pricing Strategies",
                    "description": "Optimize revenue with dynamic pricing throughout the year",
                    "keywords": ["pricing", "revenue", "seasons", "strategy"],
                    "source_url": "https://example.com/pricing-strategies"
                }
            ],
            "trend": [
                {
                    "id": 1,
                    "title": "Fall 2025 Wedding Trends",
                    "description": "Rich jewel tones and sculptural lighting dominate autumn celebrations",
                    "keywords": ["fall", "autumn", "colors", "decor", "2025"],
                    "source_url": "https://example.com/fall-2025-trends"
                },
                {
                    "id": 2,
                    "title": "Maximalist Decor Makes a Comeback",
                    "description": "Bold colors and dramatic styling replace minimalist aesthetics",
                    "keywords": ["maximalism", "decor", "bold", "styling"],
                    "source_url": "https://example.com/maximalist-weddings"
                },
                {
                    "id": 3,
                    "title": "Interactive Guest Experiences Trending",
                    "description": "From DIY cocktail bars to live art, couples want engaged guests",
                    "keywords": ["interactive", "guest experience", "entertainment"],
                    "source_url": "https://example.com/interactive-weddings"
                }
            ]
        }

        suggestions = mock_suggestions.get(section_type, [])[:num_suggestions]

        print(f"[OK] Found {len(suggestions)} {section_type} topic options")
        for i, topic in enumerate(suggestions, 1):
            print(f"   {i}. {topic['title']}")

        return suggestions

    def generate_content(self, topic: Dict, section_type: str) -> Dict:
        """
        Phase 2: Generate newsletter content for a selected topic

        Args:
            topic: Selected topic from suggest_topics()
            section_type: 'news', 'tip', or 'trend'

        Returns:
            Complete section content formatted for newsletter
        """
        print(f"\n[WRITING] Writing {section_type} content: {topic['title']}...")

        # In real implementation, this would:
        # 1. Research the topic deeply using web search
        # 2. Use AI (GPT-4o/Claude) to write content in brand voice
        # 3. Follow newsletter structure guidelines
        # 4. Include proper citations and links

        # PROTOTYPE: Return formatted mock content
        section_structure = NEWSLETTER_GUIDELINES['sections'][section_type]

        mock_content = {
            "news": {
                "title": topic['title'],
                "short_version": "61% of couples say they are open to brand sponsorships — and venues could be their billboard.",
                "whats_happening": """A recent survey revealed that 61% of Americans would accept a brand-subsidized wedding, especially if it covered 50-75% of their costs. Think: A skincare brand gifting luxury welcome bags, a spirits company sponsoring signature drinks, or even signage and shoutouts mid-ceremony. Gen Z is driving this trend, as they put less emphasis on tradition and more interest in value and novelty. The development is also fueled by increasing costs due to rising inflation and social media's influence on wedding aesthetics.""",
                "why_matters": """It opens the door to venue-brand partnerships. If a couple is comfortable having their big day "brought to you by", the venue can become a platform. Offering optional brand collabs could set your space apart — and create new revenue streams without raising rental fees.""",
                "source_url": topic['source_url']
            },
            "tip": {
                "title": topic['title'],
                "subtitle": "Make every wedding feel uniquely crafted to the individual client",
                "content": """In today's competitive wedding market, personalization is what sets standout venues apart. The first step is to utilize data to tailor communication templates and automate responses to the wedding, allowing you to free up your time to focus on genuine human connections. A strong venue management system can also streamline operations behind the scenes, giving you the bandwidth to add personal touches like custom welcome notes, curated music playlists, or small surprise upgrades that make couples and guests feel valued.

Go beyond automation by tracking insights like inquiry sources, style preferences, and guest demographics to anticipate needs before they're voiced. When your system integrates CRM, booking, and analytics tools, personalization becomes effortless — turning each event into a unique experience that feels both thoughtful and intentional.""",
                "read_more_url": topic['source_url']
            },
            "trend": {
                "title": topic['title'],
                "subtitle": "Seasonal style and experiential design dominate autumn 'I do's'",
                "content": """This year's fall weddings are embracing rich jewel tones, sculptural lighting, and guest-centered details. Couples are opting for emerald and burgundy palettes, textured florals mixing fresh and dried blooms, and cozy comforts like warm cocktails and soft throws. The overall mood is intentional and elevated — luxurious yet grounded — with sustainability and locally-sourced design at the heart of the celebration.""",
                "read_more_url": topic['source_url']
            }
        }

        content = mock_content.get(section_type, {})
        content['section_type'] = section_type
        content['generated_at'] = datetime.now().isoformat()

        print(f"[OK] Content generated ({len(content.get('content', content.get('whats_happening', '')))} characters)")

        return content

    def check_brand_guidelines(self, content: Dict) -> Dict:
        """
        Phase 5: Check content against BriteCo brand guidelines

        Args:
            content: Generated newsletter content

        Returns:
            Dictionary with pass/fail status and specific issues found
        """
        print(f"\n[CHECK] Checking brand guidelines...")

        issues = []
        warnings = []

        # Combine all text content for checking
        all_text = " ".join([str(v) for v in content.values() if isinstance(v, str)])

        # Check for forbidden terms
        forbidden = self.brand_guidelines['briteco_brand']['forbidden_terms']
        for term in forbidden:
            if term.lower() in all_text.lower():
                issues.append({
                    "severity": "error",
                    "rule": "BriteCo Brand",
                    "issue": f"Forbidden term found: '{term}'",
                    "suggestion": "Use approved terminology instead"
                })

        # Check for gendered language (wedding insurance tone)
        gendered_terms = ['bride and groom', 'bridal party', 'groomsmen', 'bridesmaid']
        for term in gendered_terms:
            if term.lower() in all_text.lower():
                corrections = self.brand_guidelines['tone']['wedding_insurance']['corrections']
                suggestion = corrections.get(term, "Use gender-neutral language")
                warnings.append({
                    "severity": "warning",
                    "rule": "Inclusive Language",
                    "issue": f"Gendered term found: '{term}'",
                    "suggestion": f"Consider using: {suggestion}"
                })

        # Check punctuation - serial comma
        import re
        # Simple check for lists without serial comma (word, word and word)
        no_serial_comma = re.findall(r'\w+,\s+\w+\s+and\s+\w+', all_text)
        if no_serial_comma:
            warnings.append({
                "severity": "warning",
                "rule": "Punctuation",
                "issue": "Possible missing serial comma",
                "suggestion": "Use serial commas in lists: 'a, b, and c'"
            })

        # Check for www.brite.co
        if 'www.brite.co' in all_text:
            issues.append({
                "severity": "error",
                "rule": "BriteCo Brand",
                "issue": "Incorrect website reference: www.brite.co",
                "suggestion": "Use brite.co or https://brite.co"
            })

        # Check for lab-grown hyphenation
        if 'lab grown' in all_text.lower() and 'lab-grown' not in all_text:
            issues.append({
                "severity": "error",
                "rule": "Punctuation",
                "issue": "'lab grown' should be hyphenated",
                "suggestion": "Use 'lab-grown'"
            })

        passed = len(issues) == 0

        result = {
            "passed": passed,
            "total_issues": len(issues),
            "total_warnings": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.now().isoformat()
        }

        # Print results
        if passed and len(warnings) == 0:
            print("[OK] All brand guidelines checks passed!")
        elif passed:
            print(f"[OK] Passed with {len(warnings)} warnings")
            for w in warnings:
                print(f"   [!] {w['issue']}")
                print(f"      -> {w['suggestion']}")
        else:
            print(f"[ERROR] Failed with {len(issues)} issues:")
            for issue in issues:
                print(f"   [X] {issue['issue']}")
                print(f"      -> {issue['suggestion']}")

        return result

    def generate_image_prompt(self, content: Dict, section_type: str) -> str:
        """
        Phase 4: Generate image prompt for Nano Banana (Gemini)

        Args:
            content: Newsletter section content
            section_type: 'news', 'tip', or 'trend'

        Returns:
            Optimized prompt for AI image generation
        """
        print(f"\n[IMAGE] Creating image prompt for {section_type} section...")

        # Extract key themes and create visual prompt
        title = content.get('title', '')

        # Style guidelines for venue newsletter images
        base_style = "Professional, elegant, modern wedding venue photography, warm natural lighting, high-end aesthetic, sophisticated composition"

        prompts = {
            "news": f"{title} - {base_style}, editorial style, newsworthy scene, subtle branding elements, contemporary venue space",
            "tip": f"{title} - {base_style}, intimate venue details, personalized touches, client-focused perspective, welcoming atmosphere",
            "trend": f"{title} - {base_style}, seasonal wedding decor, trendy color palette, stylish arrangements, inspirational setting"
        }

        prompt = prompts.get(section_type, base_style)

        print(f"[OK] Image prompt: {prompt[:100]}...")

        return prompt


def demo_workflow():
    """Demonstrate the complete newsletter generation workflow"""

    print("=" * 80)
    print("VENUE NEWSLETTER GENERATOR - PROTOTYPE DEMO")
    print("=" * 80)

    generator = NewsletterGenerator()

    # PHASE 1: Topic Suggestions
    print("\n" + "=" * 80)
    print("PHASE 1: AI SUGGESTS TOPICS")
    print("=" * 80)

    news_topics = generator.suggest_topics('news', num_suggestions=3)
    tip_topics = generator.suggest_topics('tip', num_suggestions=3)
    trend_topics = generator.suggest_topics('trend', num_suggestions=3)

    # PHASE 2: User Selection (simulated)
    print("\n" + "=" * 80)
    print("PHASE 2: GENERATE CONTENT (User selects option #1 for each)")
    print("=" * 80)

    selected_news = news_topics[0]
    selected_tip = tip_topics[0]
    selected_trend = trend_topics[0]

    news_content = generator.generate_content(selected_news, 'news')
    tip_content = generator.generate_content(selected_tip, 'tip')
    trend_content = generator.generate_content(selected_trend, 'trend')

    # PHASE 3: Content Preview
    print("\n" + "=" * 80)
    print("PHASE 3: CONTENT PREVIEW")
    print("=" * 80)

    print("\n[NEWS] NEWS SECTION:")
    print(f"   Title: {news_content['title']}")
    print(f"   Short: {news_content['short_version']}")
    print(f"   Length: {len(news_content['whats_happening'])} chars")

    print("\n[TIP] TIP SECTION:")
    print(f"   Title: {tip_content['title']}")
    print(f"   Subtitle: {tip_content['subtitle']}")
    print(f"   Length: {len(tip_content['content'])} chars")

    print("\n[TREND] TREND SECTION:")
    print(f"   Title: {trend_content['title']}")
    print(f"   Subtitle: {trend_content['subtitle']}")
    print(f"   Length: {len(trend_content['content'])} chars")

    # PHASE 4: Image Generation
    print("\n" + "=" * 80)
    print("PHASE 4: GENERATE IMAGE PROMPTS")
    print("=" * 80)

    news_image_prompt = generator.generate_image_prompt(news_content, 'news')
    tip_image_prompt = generator.generate_image_prompt(tip_content, 'tip')
    trend_image_prompt = generator.generate_image_prompt(trend_content, 'trend')

    # PHASE 5: Brand Guidelines Check
    print("\n" + "=" * 80)
    print("PHASE 5: BRAND GUIDELINES CHECK")
    print("=" * 80)

    news_check = generator.check_brand_guidelines(news_content)
    tip_check = generator.check_brand_guidelines(tip_content)
    trend_check = generator.check_brand_guidelines(trend_content)

    # Summary
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)

    total_issues = news_check['total_issues'] + tip_check['total_issues'] + trend_check['total_issues']
    total_warnings = news_check['total_warnings'] + tip_check['total_warnings'] + trend_check['total_warnings']

    print(f"\n[SUCCESS] Newsletter draft ready for review!")
    print(f"   - Total issues: {total_issues}")
    print(f"   - Total warnings: {total_warnings}")
    print(f"   - Status: {'READY FOR MANUAL QA' if total_issues == 0 else 'NEEDS FIXES'}")

    print("\n[NEXT] Next steps:")
    print("   1. User reviews content in dashboard")
    print("   2. User can edit any section")
    print("   3. User can regenerate images with custom prompts")
    print("   4. Manual QA checklist")
    print("   5. Publish to Ontraport")

    # Save to file
    output = {
        "generated_at": datetime.now().isoformat(),
        "sections": {
            "news": news_content,
            "tip": tip_content,
            "trend": trend_content
        },
        "brand_checks": {
            "news": news_check,
            "tip": tip_check,
            "trend": trend_check
        },
        "image_prompts": {
            "news": news_image_prompt,
            "tip": tip_image_prompt,
            "trend": trend_image_prompt
        }
    }

    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'newsletter_draft.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n[SAVED] Draft saved to: {output_file}")


if __name__ == "__main__":
    demo_workflow()
