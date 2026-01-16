"""
BriteCo Editorial Style Guide - Configuration
Extracted from EDITORIAL STYLE GUIDE.pdf
"""

BRAND_GUIDELINES = {
    "numbers": {
        "rules": [
            "Use the percent symbol (%) rather than typing out 'percent'",
            "For ages, use numbers rather than spelling out",
            "For zero, spell out rather than using a number",
            "For phone number, only provide BriteCo's main number: (312) 809-9100"
        ],
        "correct_examples": [
            "71% of jewelers",
            "She is 58-years-old",
            "We offer zero deductibles"
        ],
        "incorrect_patterns": [
            r"seventy[- ]one percent",
            r"fifty[- ]eight[- ]years[- ]old",
            r"\$0 deductibles"
        ]
    },

    "abbreviations": {
        "rules": [
            "For country abbreviations, do not use periods (US, UK not U.S., U.K.)",
            "For Washington, DC, do not use periods"
        ],
        "corrections": {
            r"U\.S\.": "US",
            r"U\.K\.": "UK",
            r"D\.C\.": "DC"
        }
    },

    "punctuation": {
        "rules": [
            "Use a serial comma when writing out a list",
            "Use an em dash (—) with spaces around it, not hyphen",
            "Put names of movies, books, and periodicals in italics, not quotes",
            "Put punctuation inside quotation marks",
            "Use a hyphen between two words modifying the noun",
            "Always hyphenate lab-grown"
        ],
        "correct_examples": [
            "theft, loss, and damages",
            "Engagement rings — while pricey — are a worthwhile investment",
            "Our CEO recently published on Forbes",
            'Our tagline is, "Modern protection for modern milestones."',
            "5-star ratings",
            "budget-friendly policies",
            "lab-grown diamonds"
        ],
        "incorrect_patterns": [
            r"theft, loss and damages",  # Missing serial comma
            r"—(?! )|\S—\S",  # Em dash without spaces
            r'"Forbes\."',  # Quoted periodical
            r'lab grown',  # Not hyphenated
        ]
    },

    "title_case": {
        "rules": [
            "Headlines (H1s, H2s, H3s) use Title Case",
            "All other copy uses sentence case"
        ],
        "tool": "https://titlecaseconverter.com/"
    },

    "brand_names": {
        "corrections": {
            "OMEGA Watches": "Omega Watches"
        }
    },

    "briteco_brand": {
        "do": [
            "Call BriteCo an 'insurtech company' or 'insurance provider'",
            "Refer to BriteCo as a 'specialty jewelry insurance provider' when comparing to general insurers",
            "Say 'backed by an AM Best A+ rated Insurance Carrier'",
            "Refer to website as brite.co or https://brite.co",
            "Spell it stand-alone (not standalone)"
        ],
        "dont": [
            "Call BriteCo an 'insurance company'",
            "Refer to BriteCo as 'specialized jewelry insurance'",
            "Slander competitors or link to them (e.g. Jewelers Mutual)",
            "Say 'we have AM Best policies' or 'we are AM Best'",
            "Refer to website as www.brite.co",
            "Use standalone or stand-alone"
        ],
        "forbidden_terms": [
            "insurance company",
            "specialized jewelry insurance",
            "AM Best policies",
            "we are AM Best",
            "www.brite.co"
        ],
        "required_terms": {
            "insurtech company": ["insurance company"],
            "insurance provider": ["insurance company"],
            "specialty jewelry insurance provider": ["specialized jewelry insurance"],
            "backed by an AM Best A+ rated Insurance Carrier": ["AM Best policies", "we are AM Best"],
            "brite.co": ["www.brite.co"],
            "https://brite.co": ["www.brite.co"]
        }
    },

    "tone": {
        "wedding_insurance": {
            "rules": [
                "Be inclusive and use gender-less verbiage (they, them, theirs)",
                "Use 'wedding party' rather than 'bridal party'",
                "Say 'groom crew' over 'groomsmen'",
                "Rather than bride and groom, say partner, soon-to-be spouse"
            ],
            "corrections": {
                "bridal party": "wedding party",
                "groomsmen": "groom crew",
                "bride and groom": "partner",
                "bride": "partner",
                "groom": "partner"
            }
        },
        "jewelry": {
            "rules": [
                "When mentioning health claims, never promise results",
                "Use softer language: 'is known for', 'may be helpful with', 'has been seen to'"
            ],
            "avoid_patterns": [
                r"will increase",
                r"will boost",
                r"guarantees",
                r"proven to"
            ]
        }
    },

    "glossary": {
        "correct_terms": {
            "Homeowners policy": ["Homeowner's", "Homeowners'"],
            "Renters insurance": ["Renter's", "Renters'"],
            "stand-alone": ["standalone", "stand alone"]  # Note: PDF shows inconsistency
        }
    }
}

# Brand voice characteristics for AI content generation
BRAND_VOICE = {
    "tone": "Professional but warm, informative, approachable",
    "style": "Clear, concise, helpful",
    "perspective": "We help venue professionals succeed",
    "avoid": [
        "Overly salesy language",
        "Jargon without explanation",
        "Promises we can't keep",
        "Gendered language",
        "Competitor comparisons"
    ]
}

# Newsletter-specific guidelines
NEWSLETTER_GUIDELINES = {
    "sections": {
        "news": {
            "structure": [
                "The Short Version: [one sentence summary]",
                "What's Happening: [2-3 paragraphs]",
                "Why It Matters for Venues: [practical takeaway]"
            ],
            "tone": "Informative, newsworthy, relevant to venues"
        },
        "tip": {
            "structure": [
                "Title",
                "Subtitle: [actionable summary]",
                "Content: [2-3 paragraphs]",
                "CTA: Read More →"
            ],
            "tone": "Helpful, actionable, expert advice"
        },
        "trend": {
            "structure": [
                "Title",
                "Subtitle: [trend description]",
                "Content: [2-3 paragraphs]",
                "CTA: Read More →"
            ],
            "tone": "Trend-forward, seasonal, inspiring"
        }
    },
    "formatting": {
        "headlines": "Title Case",
        "body": "Sentence case",
        "sections": "Use italics for section labels"
    }
}


def get_style_guide_for_prompt(section_type=None):
    """
    Generate a prompt-friendly style guide string from the brand guidelines config.

    Args:
        section_type: Optional - 'news', 'tip', or 'trend' to include section-specific structure

    Returns:
        Formatted string ready to include in AI prompts
    """
    guide = "## EDITORIAL STYLE GUIDE\n\n"

    # Numbers
    guide += "### NUMBERS\n"
    for rule in BRAND_GUIDELINES["numbers"]["rules"]:
        guide += f"- {rule}\n"
    guide += "Examples: " + ", ".join(BRAND_GUIDELINES["numbers"]["correct_examples"]) + "\n\n"

    # Punctuation
    guide += "### PUNCTUATION\n"
    for rule in BRAND_GUIDELINES["punctuation"]["rules"]:
        guide += f"- {rule}\n"
    guide += "Examples: " + ", ".join(f'"{ex}"' for ex in BRAND_GUIDELINES["punctuation"]["correct_examples"][:4]) + "\n\n"

    # Abbreviations
    guide += "### ABBREVIATIONS\n"
    for rule in BRAND_GUIDELINES["abbreviations"]["rules"]:
        guide += f"- {rule}\n"
    guide += "\n"

    # Title Case
    guide += "### TITLE CASE\n"
    for rule in BRAND_GUIDELINES["title_case"]["rules"]:
        guide += f"- {rule}\n"
    guide += "\n"

    # Inclusive Language (from wedding_insurance tone)
    guide += "### INCLUSIVE LANGUAGE (REQUIRED)\n"
    for rule in BRAND_GUIDELINES["tone"]["wedding_insurance"]["rules"]:
        guide += f"- {rule}\n"
    guide += "\n"

    # Health/Promise Claims (from jewelry tone)
    guide += "### CLAIMS & PROMISES\n"
    for rule in BRAND_GUIDELINES["tone"]["jewelry"]["rules"]:
        guide += f"- {rule}\n"
    guide += "\n"

    # BriteCo Brand Rules
    guide += "### BRITECO BRAND TERMINOLOGY\n"
    guide += "DO:\n"
    for rule in BRAND_GUIDELINES["briteco_brand"]["do"]:
        guide += f"  - {rule}\n"
    guide += "DON'T:\n"
    for rule in BRAND_GUIDELINES["briteco_brand"]["dont"]:
        guide += f"  - {rule}\n"
    guide += "\n"

    # Glossary
    guide += "### GLOSSARY (Correct Spellings)\n"
    for correct, incorrect_list in BRAND_GUIDELINES["glossary"]["correct_terms"].items():
        guide += f"- Use \"{correct}\" (not {', '.join(incorrect_list)})\n"
    guide += "\n"

    # Brand Voice
    guide += "### TONE & VOICE\n"
    guide += f"- Tone: {BRAND_VOICE['tone']}\n"
    guide += f"- Style: {BRAND_VOICE['style']}\n"
    guide += f"- Perspective: {BRAND_VOICE['perspective']}\n"
    guide += "- AVOID: " + ", ".join(BRAND_VOICE['avoid']) + "\n"

    # Section-specific structure if requested
    if section_type and section_type in NEWSLETTER_GUIDELINES["sections"]:
        section = NEWSLETTER_GUIDELINES["sections"][section_type]
        guide += f"\n### {section_type.upper()} SECTION STRUCTURE\n"
        for item in section["structure"]:
            guide += f"- {item}\n"
        guide += f"- Tone: {section['tone']}\n"
        # Add formatting guidelines
        guide += f"\n### FORMATTING\n"
        guide += f"- Headlines: {NEWSLETTER_GUIDELINES['formatting']['headlines']}\n"
        guide += f"- Body: {NEWSLETTER_GUIDELINES['formatting']['body']}\n"
        guide += f"- Section labels: {NEWSLETTER_GUIDELINES['formatting']['sections']}\n"

    return guide


def get_section_structure(section_type):
    """
    Get the structure requirements for a specific newsletter section.

    Args:
        section_type: 'news', 'tip', or 'trend'

    Returns:
        Dict with structure and tone info
    """
    if section_type in NEWSLETTER_GUIDELINES["sections"]:
        return NEWSLETTER_GUIDELINES["sections"][section_type]
    return None
