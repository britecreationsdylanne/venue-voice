"""
Functional Demo API Server
Provides real AI-powered endpoints for the interactive demo
Run this to make the demo fully functional!
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from integrations.openai_client import OpenAIClient
from integrations.gemini_client import GeminiClient
from integrations.claude_client import ClaudeClient
from integrations.perplexity_client import PerplexityClient
# NOTE: Brave Search deprecated - using OpenAI with site: operators instead
from config.brand_guidelines import BRAND_VOICE, NEWSLETTER_GUIDELINES, get_style_guide_for_prompt
from config.model_config import get_model_config, get_model_for_task

app = Flask(__name__, static_folder='.')
CORS(app)

# Helper function to safely print Unicode content on Windows
def safe_print(text):
    """Print text with proper encoding handling for Windows console"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacement character
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)

# Helper function to convert HTML to plain text
def html_to_plain_text(html_content):
    """Convert HTML newsletter content to plain text for Ontraport"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)

    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text

# Initialize AI clients
openai_client = OpenAIClient()
gemini_client = GeminiClient()

# Try to initialize Claude (optional)
try:
    claude_client = ClaudeClient()
    print("[OK] Claude initialized")
except Exception as e:
    claude_client = None
    print(f"[WARNING] Claude not available: {e}")

# NOTE: Brave Search deprecated - using OpenAI with site: operators for Source Explorer
brave_client = None

# Initialize Perplexity client
try:
    perplexity_client = PerplexityClient()
except Exception as e:
    perplexity_client = None
    print(f"[WARNING] Perplexity not available: {e}")

# Seasonal data for trends
SEASONAL_TRENDS = {
    "january": {
        "season": "winter",
        "trends": [
            "Winter Wedding Micro-Moments: Intimate Gatherings on the Rise",
            "New Year, New Venues: Post-Holiday Booking Surge",
            "Cozy Luxury: Fireplaces & Candlelight Taking Center Stage"
        ]
    },
    "february": {
        "season": "winter",
        "trends": [
            "Valentine's Day Proposals Drive Spring Bookings",
            "Winter Romance: Snowy Venue Photography Trends",
            "Last-Minute Winter Wedding Packages Selling Fast"
        ]
    },
    "march": {
        "season": "spring",
        "trends": [
            "Spring Awakening: Garden Venue Inquiries Up 45%",
            "Pastel Palettes Return for Spring 2026 Weddings",
            "Unpredictable Weather: Backup Plan Requests Increasing"
        ]
    },
    "april": {
        "season": "spring",
        "trends": [
            "Cherry Blossom Season: Outdoor Ceremonies Peak",
            "Spring Showers, Wedding Flowers: Rain Plan Essentials",
            "Earth Day Influence: Eco-Friendly Venues in Demand"
        ]
    },
    "may": {
        "season": "spring",
        "trends": [
            "Peak Wedding Season Begins: Venues at 90% Capacity",
            "Mother's Day Impact: Family-Focused Celebrations Rise",
            "Memorial Day Weekend: Extended Celebration Bookings"
        ]
    },
    "june": {
        "season": "summer",
        "trends": [
            "June Wedding Rush: Traditional Peak Season Returns",
            "Longer Days = Extended Receptions & Late-Night Dancing",
            "Outdoor Everything: Venues Adding More Al Fresco Options"
        ]
    },
    "july": {
        "season": "summer",
        "trends": [
            "Patriotic Weekend Celebrations: July 4th Week Bookings",
            "Heat Wave Solutions: Venues Investing in Cooling Systems",
            "Summer Camp Vibes: Nostalgic Themed Weddings Trending"
        ]
    },
    "august": {
        "season": "summer",
        "trends": [
            "Late Summer Romance: Back-to-School Nostalgia in Decor",
            "Golden Hour Obsession: Sunset Ceremony Timing Crucial",
            "August Availability: Couples Discovering the Hidden Gem Month"
        ]
    },
    "september": {
        "season": "fall",
        "trends": [
            "Fall Foliage Fever: Rustic Venues Fully Booked",
            "Second Peak Season: September Surpasses June in Some Markets",
            "Harvest-Inspired Details: Farm-to-Table Taking Over"
        ]
    },
    "october": {
        "season": "fall",
        "trends": [
            "Fall Micro-Weddings Are Here to Stay",
            "October Magic: Halloween-Adjacent Celebrations Trending",
            "Apple Orchard & Vineyard Venues: Seasonal Activities Integrated"
        ]
    },
    "november": {
        "season": "fall",
        "trends": [
            "Thanksgiving Week Bookings: Family-Reunion Style Weddings",
            "Gratitude Themes: Thankfulness Woven into Ceremonies",
            "Holiday Preview: Festive Decor Starting Early"
        ]
    },
    "december": {
        "season": "winter",
        "trends": [
            "Holiday Weddings: Decor Already Done for You",
            "New Year's Eve Celebrations: Midnight Kiss Ceremonies",
            "Winter Wonderland: Venues Maximizing Existing Holiday Setup"
        ]
    }
}

@app.route('/')
def serve_demo():
    """Serve the new API-connected demo"""
    return send_from_directory('.', 'index.html')

@app.route('/old-demo')
def serve_old_demo():
    """Serve the old static demo"""
    return send_from_directory('.', 'INTERACTIVE_DEMO.html')

@app.route('/briteco_template.html')
def serve_template():
    """Serve the Briteco newsletter HTML template"""
    return send_from_directory('.', 'briteco_template.html')

@app.route('/api/search-news', methods=['POST'])
def search_news():
    """Search for recent wedding industry news using OpenAI Responses API"""
    try:
        data = request.json
        month = data.get('month', 'january')
        exclude_urls = data.get('exclude_urls', [])

        print(f"\n[API] Searching web for news with OpenAI Responses API (month: {month})...")

        # Use OpenAI Responses API - get 15 real articles, NO FALLBACK TO FAKE ARTICLES
        try:
            print("[API] Using OpenAI Responses API for 15 real articles...")

            search_results = openai_client.search_wedding_news(month, exclude_urls=exclude_urls)

            # Transform url to source_url for frontend compatibility
            for result in search_results:
                result['source_url'] = result.get('url', '')

            articles = search_results[:15]  # Return up to 15 articles

            if len(articles) > 0:
                print(f"[API] OpenAI Responses API returned {len(articles)} REAL articles")
                return jsonify({
                    'success': True,
                    'articles': articles,
                    'source': 'openai_responses_api',
                    'generated_at': datetime.now().isoformat()
                })
            else:
                print(f"[API ERROR] OpenAI Responses API returned 0 articles - NO FALLBACK")
                return jsonify({
                    'success': False,
                    'error': 'No articles found from web search',
                    'articles': [],
                    'generated_at': datetime.now().isoformat()
                }), 500
        except Exception as e:
            print(f"[API ERROR] OpenAI Responses API failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'articles': [],
                'generated_at': datetime.now().isoformat()
            }), 500

        # REMOVED: No more fallback to fake articles pool

        # ALL POSSIBLE ARTICLES - 25 different articles
        all_articles = [
                {"title": "Wedding Venue Booking Trends Shift in 2025", "description": "Data shows 67% of couples now book venues 18+ months in advance", "keywords": ["booking", "trends", "data", month], "source_url": "https://www.theknot.com", "age": "2 weeks ago"},
                {"title": "Virtual Tours Increase Venue Inquiries by 40%", "description": "3D venue tours converting better than traditional photo galleries", "keywords": ["virtual tours", "technology", "conversion", month], "source_url": "https://www.weddingwire.com", "age": "1 week ago"},
                {"title": "Gen Z Couples Prioritize Instagram-Worthy Venues", "description": "Social media appeal now top factor for 58% of younger couples", "keywords": ["Gen Z", "social media", "Instagram", month], "source_url": "https://www.brides.com", "age": "3 days ago"},
                {"title": "Wedding Venue Revenue Up 25% with AI Booking Tools", "description": "Automated scheduling and chatbots driving venue profitability", "keywords": ["AI", "revenue", "automation", month], "source_url": "https://www.theknot.com", "age": "1 week ago"},
                {"title": "Sustainable Wedding Venues See 35% Growth", "description": "Eco-conscious couples seeking green-certified event spaces", "keywords": ["sustainability", "eco-friendly", "growth", month], "source_url": "https://www.marthastewartweddings.com", "age": "4 days ago"},
                {"title": "Micro-Weddings Continue Strong in 2026", "description": "Small intimate gatherings remain popular despite pandemic ending", "keywords": ["micro-weddings", "trends", "intimate", month], "source_url": "https://www.theknot.com", "age": "1 week ago"},
                {"title": "Wedding Venue Tech Investment Pays Off", "description": "Venues with digital tools see 50% faster booking cycles", "keywords": ["technology", "investment", "booking", month], "source_url": "https://www.weddingwire.com", "age": "5 days ago"},
                {"title": "Hybrid Wedding Venues Gaining Traction", "description": "Spaces offering both indoor and outdoor options in high demand", "keywords": ["hybrid", "indoor-outdoor", "flexibility", month], "source_url": "https://www.brides.com", "age": "2 weeks ago"},
                {"title": "Dynamic Pricing Boosts Venue Revenue", "description": "Seasonal and demand-based pricing increases profits by 30%", "keywords": ["pricing", "revenue", "strategy", month], "source_url": "https://www.theknot.com", "age": "6 days ago"},
                {"title": "Wedding Venue Video Marketing Drives Bookings", "description": "Short-form venue videos on TikTok and Instagram Reels converting at 3x rate", "keywords": ["video", "marketing", "TikTok", month], "source_url": "https://www.marthastewartweddings.com", "age": "1 week ago"},
                {"title": "Destination Wedding Venues Report 50% Revenue Increase", "description": "Travel restrictions lifting drives demand for international venue bookings", "keywords": ["destination", "travel", "international", month], "source_url": "https://www.brides.com", "age": "3 days ago"},
                {"title": "All-Inclusive Venue Packages Simplify Planning", "description": "Couples prefer one-stop-shop venues that handle everything", "keywords": ["all-inclusive", "packages", "planning", month], "source_url": "https://www.theknot.com", "age": "2 days ago"},
                {"title": "Wedding Venues Embrace Contactless Check-In", "description": "Digital guest management systems improve arrival experience", "keywords": ["contactless", "digital", "guest management", month], "source_url": "https://www.weddingwire.com", "age": "1 week ago"},
                {"title": "Venues with In-House Catering See Higher Profit Margins", "description": "Controlling food service drives 40% revenue increase for venue owners", "keywords": ["catering", "profit", "revenue", month], "source_url": "https://www.theknot.com", "age": "4 days ago"},
                {"title": "Outdoor Wedding Venues Dominate 2025 Bookings", "description": "75% of couples prefer outdoor or garden venue settings", "keywords": ["outdoor", "garden", "nature", month], "source_url": "https://www.brides.com", "age": "1 week ago"},
                {"title": "Wedding Venue SEO Strategies That Actually Work", "description": "Local search optimization increases venue inquiries by 60%", "keywords": ["SEO", "marketing", "local search", month], "source_url": "https://www.weddingwire.com", "age": "5 days ago"},
                {"title": "Flexible Cancellation Policies Win More Bookings", "description": "Venues offering flexibility see 45% higher conversion rates", "keywords": ["flexibility", "cancellation", "booking", month], "source_url": "https://www.theknot.com", "age": "3 days ago"},
                {"title": "Wedding Venues Leverage User-Generated Content", "description": "Guest photos and reviews drive 3x more inquiries than professional shots", "keywords": ["UGC", "social proof", "marketing", month], "source_url": "https://www.marthastewartweddings.com", "age": "2 weeks ago"},
                {"title": "Boutique Venues Outperform Large Event Spaces", "description": "Intimate settings command premium pricing and higher satisfaction", "keywords": ["boutique", "intimate", "premium", month], "source_url": "https://www.brides.com", "age": "6 days ago"},
                {"title": "Wedding Venue Email Marketing Sees 35% Open Rates", "description": "Personalized drip campaigns converting prospects to bookings", "keywords": ["email", "marketing", "conversion", month], "source_url": "https://www.weddingwire.com", "age": "1 week ago"},
                {"title": "Venues Adding Bridal Suites See Booking Boost", "description": "Getting-ready spaces become must-have amenity for couples", "keywords": ["bridal suite", "amenities", "booking", month], "source_url": "https://www.theknot.com", "age": "4 days ago"},
                {"title": "Same-Day Venue Tours Convert at 80% Rate", "description": "Instant availability for site visits dramatically increases bookings", "keywords": ["tours", "conversion", "availability", month], "source_url": "https://www.weddingwire.com", "age": "2 days ago"},
                {"title": "Wedding Venue Chatbots Answer 70% of Inquiries", "description": "AI assistants handle common questions, freeing staff for bookings", "keywords": ["chatbot", "AI", "automation", month], "source_url": "https://www.brides.com", "age": "1 week ago"},
                {"title": "Rustic Barn Venues Lead 2026 Popularity Rankings", "description": "Countryside aesthetics remain top choice for modern couples", "keywords": ["rustic", "barn", "countryside", month], "source_url": "https://www.marthastewartweddings.com", "age": "5 days ago"},
                {"title": "Venue Comparison Tools Influence 90% of Bookings", "description": "Couples research average 8 venues before making final decision", "keywords": ["comparison", "research", "decision", month], "source_url": "https://www.theknot.com", "age": "3 days ago"}
        ]

        # Filter out excluded titles FIRST
        available_articles = [a for a in all_articles if a['title'] not in exclude_titles]

        # If we've shown everything, reset and shuffle
        if len(available_articles) < 5:
            print("[API] All articles shown, using full set with shuffle")
            available_articles = all_articles.copy()

        # Shuffle for randomness
        import random as rand_module
        rand_module.shuffle(available_articles)

        # Take first 5
        articles = available_articles[:5]

        print(f"[API] Returning {len(articles)} articles")

        return jsonify({
            'success': True,
            'articles': articles,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search-tips', methods=['POST'])
def search_tips():
    """Search for venue management tips using OpenAI Responses API"""
    try:
        data = request.json
        month = data.get('month', 'january')
        exclude_urls = data.get('exclude_urls', [])

        print(f"\n[API] Searching web for venue tips with OpenAI Responses API (month: {month})...")

        # Use OpenAI Responses API - get 15 real tips, NO FALLBACK TO FAKE TIPS
        try:
            print("[API] Using OpenAI Responses API for 15 real tips...")

            search_results = openai_client.search_wedding_tips(month, exclude_urls=exclude_urls)

            # Transform url to source_url for frontend compatibility
            for result in search_results:
                result['source_url'] = result.get('url', '')

            tips = search_results[:15]  # Return up to 15 tips

            if len(tips) > 0:
                print(f"[API] OpenAI Responses API returned {len(tips)} REAL tips")
                return jsonify({
                    'success': True,
                    'tips': tips,
                    'source': 'openai_responses_api',
                    'generated_at': datetime.now().isoformat()
                })
            else:
                print(f"[API ERROR] OpenAI Responses API returned 0 tips - NO FALLBACK")
                return jsonify({
                    'success': False,
                    'error': 'No tips found from web search',
                    'tips': [],
                    'generated_at': datetime.now().isoformat()
                }), 500
        except Exception as e:
            print(f"[API ERROR] OpenAI Responses API failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'tips': [],
                'generated_at': datetime.now().isoformat()
            }), 500

        # REMOVED: No more fallback to fake tips pool

        # ALL POSSIBLE TIPS - 20 different tip articles
        all_tips = [
                {"title": "Transform Your Virtual Tours with These 5 Quick Wins", "description": "Improve conversion rates by showing venues from guest perspective", "keywords": ["virtual tours", "conversion", "technology"], "source_url": "https://www.theknot.com", "age": "1 week ago"},
                {"title": "Automate Your Follow-Up Emails to Book More Tours", "description": "Drip campaigns that convert inquiries into site visits", "keywords": ["email", "automation", "follow-up"], "source_url": "https://www.weddingwire.com", "age": "3 days ago"},
                {"title": "Optimize Your Google Business Profile for More Leads", "description": "Local SEO tactics that put your venue on the map", "keywords": ["Google", "SEO", "local"], "source_url": "https://www.brides.com", "age": "5 days ago"},
                {"title": "Create an Instagram Strategy That Books Weddings", "description": "Social media content calendar for venue marketing", "keywords": ["Instagram", "social media", "content"], "source_url": "https://www.theknot.com", "age": "2 weeks ago"},
                {"title": "Turn Past Couples into Your Best Marketing Asset", "description": "Referral program strategies that generate qualified leads", "keywords": ["referrals", "testimonials", "marketing"], "source_url": "https://www.marthastewartweddings.com", "age": "4 days ago"},
                {"title": "Price Your Venue Packages for Maximum Profit", "description": "Dynamic pricing strategies that increase revenue per booking", "keywords": ["pricing", "packages", "revenue"], "source_url": "https://www.weddingwire.com", "age": "1 week ago"},
                {"title": "Reduce No-Shows with Smart Booking Deposits", "description": "Payment structures that secure committed couples", "keywords": ["deposits", "payments", "booking"], "source_url": "https://www.theknot.com", "age": "6 days ago"},
                {"title": "Create a Venue Tour Experience That Closes Deals", "description": "Site visit best practices that convert 80% of prospects", "keywords": ["tours", "conversion", "sales"], "source_url": "https://www.brides.com", "age": "2 days ago"},
                {"title": "Use Video Marketing to Showcase Your Venue", "description": "TikTok and Reels strategies for wedding venue promotion", "keywords": ["video", "TikTok", "marketing"], "source_url": "https://www.weddingwire.com", "age": "1 week ago"},
                {"title": "Implement a CRM System to Track Every Lead", "description": "Customer relationship tools that prevent lost opportunities", "keywords": ["CRM", "leads", "tracking"], "source_url": "https://www.theknot.com", "age": "5 days ago"},
                {"title": "Partner with Local Vendors for Cross-Promotion", "description": "Collaborative marketing that expands your reach", "keywords": ["partnerships", "vendors", "promotion"], "source_url": "https://www.marthastewartweddings.com", "age": "3 days ago"},
                {"title": "Respond to Inquiries in Under 5 Minutes", "description": "Speed-to-lead strategies that win more bookings", "keywords": ["response time", "inquiries", "conversion"], "source_url": "https://www.brides.com", "age": "1 week ago"},
                {"title": "Build an Email List from Website Visitors", "description": "Lead magnet strategies that grow your database", "keywords": ["email list", "lead generation", "content"], "source_url": "https://www.weddingwire.com", "age": "4 days ago"},
                {"title": "Create Seasonal Promotions That Fill Your Calendar", "description": "Strategic discounting that drives off-season bookings", "keywords": ["promotions", "seasonal", "discounts"], "source_url": "https://www.theknot.com", "age": "2 weeks ago"},
                {"title": "Showcase Real Weddings in Your Marketing", "description": "User-generated content that builds trust with couples", "keywords": ["real weddings", "UGC", "authenticity"], "source_url": "https://www.brides.com", "age": "6 days ago"},
                {"title": "Optimize Your Website for Mobile Bookings", "description": "Mobile-first design that captures on-the-go couples", "keywords": ["mobile", "website", "UX"], "source_url": "https://www.weddingwire.com", "age": "3 days ago"},
                {"title": "Track Your Marketing ROI with Simple Metrics", "description": "Key performance indicators every venue should monitor", "keywords": ["analytics", "ROI", "metrics"], "source_url": "https://www.theknot.com", "age": "1 week ago"},
                {"title": "Create a Signature Venue Package That Sells Itself", "description": "All-inclusive offerings that simplify decision-making", "keywords": ["packages", "all-inclusive", "sales"], "source_url": "https://www.marthastewartweddings.com", "age": "5 days ago"},
                {"title": "Use Retargeting Ads to Re-Engage Lost Leads", "description": "Facebook and Instagram ads that bring couples back", "keywords": ["retargeting", "ads", "Facebook"], "source_url": "https://www.weddingwire.com", "age": "2 days ago"},
                {"title": "Build a Content Calendar for Consistent Posting", "description": "Social media planning that maintains engagement", "keywords": ["content calendar", "planning", "consistency"], "source_url": "https://www.brides.com", "age": "1 week ago"}
        ]

        # Filter out excluded titles FIRST
        available_tips = [t for t in all_tips if t['title'] not in exclude_titles]

        # If we've shown everything, reset
        if len(available_tips) < 5:
            print("[API] All tips shown, using full set")
            available_tips = all_tips.copy()

        # Shuffle for randomness
        import random as rand_module
        rand_module.shuffle(available_tips)

        # Take first 5
        tips = available_tips[:5]

        print(f"[API] Found {len(tips)} tip articles")

        return jsonify({
            'success': True,
            'tips': tips,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-trends', methods=['POST'])
def get_trends():
    """Search for wedding trends using OpenAI Responses API"""
    try:
        data = request.json
        month = data.get('month', 'january').lower()
        exclude_urls = data.get('exclude_urls', [])

        # Get season for this month
        month_to_season = {
            'january': 'winter', 'february': 'winter', 'december': 'winter',
            'march': 'spring', 'april': 'spring', 'may': 'spring',
            'june': 'summer', 'july': 'summer', 'august': 'summer',
            'september': 'fall', 'october': 'fall', 'november': 'fall'
        }
        season = month_to_season.get(month, 'spring')

        print(f"\n[API] Searching web for {season} wedding trends with OpenAI Responses API ({month})...")

        # Use OpenAI Responses API - get 15 real trends, NO FALLBACK TO FAKE TRENDS
        try:
            print("[API] Using OpenAI Responses API for 15 real trends...")

            search_results = openai_client.search_wedding_trends(month, season, exclude_urls=exclude_urls)

            # Add season and transform url to source_url for frontend compatibility
            for trend in search_results:
                if 'season' not in trend:
                    trend['season'] = season
                trend['source_url'] = trend.get('url', '')

            trends = search_results[:15]  # Return up to 15 trends

            if len(trends) > 0:
                print(f"[API] OpenAI Responses API returned {len(trends)} REAL trends for {season}")
                return jsonify({
                    'success': True,
                    'trends': trends,
                    'season': season,
                    'source': 'openai_responses_api',
                    'generated_at': datetime.now().isoformat()
                })
            else:
                print(f"[API ERROR] OpenAI Responses API returned 0 trends - NO FALLBACK")
                return jsonify({
                    'success': False,
                    'error': 'No trends found from web search',
                    'trends': [],
                    'season': season,
                    'generated_at': datetime.now().isoformat()
                }), 500
        except Exception as e:
            print(f"[API ERROR] OpenAI Responses API failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'trends': [],
                'season': season,
                'generated_at': datetime.now().isoformat()
            }), 500

        # REMOVED: No more fallback to fake trends pool

        # ALL POSSIBLE TRENDS - 24 different trend articles
        all_trends = [
                {"title": "Maximalist Decor Makes Bold Comeback", "description": "Couples embrace vibrant colors and eclectic styling", "keywords": [season, "maximalist", "decor"], "source_url": "https://www.brides.com", "season": season, "age": "1 week ago"},
                {"title": "Sustainable Weddings Go Mainstream", "description": "Eco-friendly choices now expected, not optional", "keywords": [season, "sustainable", "eco-friendly"], "source_url": "https://www.theknot.com", "season": season, "age": "3 days ago"},
                {"title": "Multi-Day Wedding Celebrations Trending", "description": "Extended festivities replace single-day events", "keywords": [season, "multi-day", "celebration"], "source_url": "https://www.weddingwire.com", "season": season, "age": "5 days ago"},
                {"title": "Personalized Menus Replace Traditional Catering", "description": "Custom dining experiences reflect couple's story", "keywords": [season, "menu", "catering"], "source_url": "https://www.marthastewartweddings.com", "season": season, "age": "2 weeks ago"},
                {"title": "Live Music Dominates Reception Entertainment", "description": "Bands and musicians preferred over DJ setups", "keywords": [season, "live music", "entertainment"], "source_url": "https://www.theknot.com", "season": season, "age": "4 days ago"},
                {"title": "Intimate Guest Lists Under 50 People", "description": "Quality over quantity drives smaller celebrations", "keywords": [season, "intimate", "small wedding"], "source_url": "https://www.brides.com", "season": season, "age": "1 week ago"},
                {"title": "Dried Florals Replace Fresh Flower Arrangements", "description": "Sustainable and budget-friendly botanical choices", "keywords": [season, "dried flowers", "florals"], "source_url": "https://www.weddingwire.com", "season": season, "age": "6 days ago"},
                {"title": "Interactive Food Stations Engage Guests", "description": "Build-your-own bars and live cooking demonstrations", "keywords": [season, "food stations", "interactive"], "source_url": "https://www.theknot.com", "season": season, "age": "2 days ago"},
                {"title": "Mismatched Bridesmaid Dresses Gain Popularity", "description": "Coordinated colors with individual style choices", "keywords": [season, "bridesmaids", "fashion"], "source_url": "https://www.brides.com", "season": season, "age": "1 week ago"},
                {"title": "Unplugged Ceremonies Become Standard Request", "description": "Couples ask guests to put away phones and cameras", "keywords": [season, "unplugged", "ceremony"], "source_url": "https://www.marthastewartweddings.com", "season": season, "age": "5 days ago"},
                {"title": "Bold Accent Colors Replace All-White Palettes", "description": "Jewel tones and vibrant hues make statements", "keywords": [season, "colors", "palette"], "source_url": "https://www.weddingwire.com", "season": season, "age": "3 days ago"},
                {"title": "Dessert Bars Compete with Traditional Wedding Cakes", "description": "Variety of sweets appeals to diverse tastes", "keywords": [season, "dessert", "cake"], "source_url": "https://www.theknot.com", "season": season, "age": "1 week ago"},
                {"title": "Lounge Seating Areas Enhance Guest Experience", "description": "Comfortable furniture creates conversation spaces", "keywords": [season, "lounge", "seating"], "source_url": "https://www.brides.com", "season": season, "age": "4 days ago"},
                {"title": "Non-Traditional Venues Outpace Hotels and Ballrooms", "description": "Barns, lofts, and outdoor spaces preferred", "keywords": [season, "venue", "alternative"], "source_url": "https://www.weddingwire.com", "season": season, "age": "2 weeks ago"},
                {"title": "Signature Cocktails Reflect Couple's Personality", "description": "Custom drink menus add personal touch", "keywords": [season, "cocktails", "bar"], "source_url": "https://www.theknot.com", "season": season, "age": "6 days ago"},
                {"title": "Bridal Jumpsuits and Pantsuits Rise in Popularity", "description": "Modern alternatives to traditional gowns", "keywords": [season, "bridal fashion", "jumpsuit"], "source_url": "https://www.brides.com", "season": season, "age": "1 week ago"},
                {"title": "Vintage and Antique Decor Elements Return", "description": "Nostalgic touches add character and charm", "keywords": [season, "vintage", "antique"], "source_url": "https://www.marthastewartweddings.com", "season": season, "age": "5 days ago"},
                {"title": "Cultural Fusion Weddings Celebrate Heritage", "description": "Blending traditions creates meaningful ceremonies", "keywords": [season, "cultural", "traditions"], "source_url": "https://www.weddingwire.com", "season": season, "age": "3 days ago"},
                {"title": "Micro-Moments Replace Formal Photo Sessions", "description": "Candid photography captures authentic emotions", "keywords": [season, "photography", "candid"], "source_url": "https://www.theknot.com", "season": season, "age": "1 week ago"},
                {"title": "Late-Night Snack Stations Keep Party Going", "description": "Pizza, tacos, and comfort food for dancing guests", "keywords": [season, "late night", "food"], "source_url": "https://www.brides.com", "season": season, "age": "4 days ago"},
                {"title": "Statement Lighting Transforms Venue Ambiance", "description": "Chandeliers, string lights, and LEDs set mood", "keywords": [season, "lighting", "ambiance"], "source_url": "https://www.weddingwire.com", "season": season, "age": "2 days ago"},
                {"title": "Weekday Weddings Offer Better Value and Availability", "description": "Monday-Thursday events grow more common", "keywords": [season, "weekday", "budget"], "source_url": "https://www.theknot.com", "season": season, "age": "1 week ago"},
                {"title": "Garden-Style Centerpieces Bring Nature Indoors", "description": "Organic arrangements with greenery and wildflowers", "keywords": [season, "centerpieces", "garden"], "source_url": "https://www.marthastewartweddings.com", "season": season, "age": "5 days ago"},
                {"title": "Couples Prioritize Guest Comfort Over Formality", "description": "Relaxed dress codes and flexible timelines", "keywords": [season, "comfort", "casual"], "source_url": "https://www.brides.com", "season": season, "age": "3 days ago"}
        ]

        # Filter out excluded titles FIRST
        available_trends = [t for t in all_trends if t['title'] not in exclude_titles]

        # If we've shown everything, reset
        if len(available_trends) < 5:
            print("[API] All trends shown, using full set")
            available_trends = all_trends.copy()

        # Shuffle for randomness
        import random as rand_module
        rand_module.shuffle(available_trends)

        # Take first 5
        trends = available_trends[:5]

        print(f"[API] Found {len(trends)} trend articles for {season}")

        return jsonify({
            'success': True,
            'trends': trends,
            'season': season,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/research-articles', methods=['POST'])
def research_articles():
    """
    GPT-5.2 researches selected articles and produces detailed summaries.
    - NEWS: One-page briefing (~400-500 words)
    - TIP: Half-page briefing (~200-250 words)
    - TREND: Half-page briefing (~200-250 words)
    """
    try:
        data = request.json
        news_topic = data.get('news_topic')
        tip_topic = data.get('tip_topic')
        trend_topic = data.get('trend_topic')

        print(f"\n[API] Researching articles with GPT-5.2...")

        research_results = {}

        # Research NEWS article (One-Pager ~400-500 words)
        if news_topic:
            safe_print(f"  - Researching NEWS: {news_topic.get('title', 'Unknown')}")
            news_research_prompt = f"""You are a senior industry analyst. Research this article and produce a one-page briefing (~400-500 words) for newsletter writers.

Article: {news_topic.get('title', 'Unknown')}
Source: {news_topic.get('url', 'N/A')}
Initial Summary: {news_topic.get('description', '')}
Additional Context: {news_topic.get('so_what', '')}

Produce a structured briefing with these sections:

1. EXECUTIVE SUMMARY
Write 2-3 sentences capturing the core news and its significance.

2. KEY FACTS & DATA
Provide bullet points with specific statistics, dates, percentages, and quoted facts from the article.

3. INDUSTRY CONTEXT
Write 1 paragraph explaining why this matters in the broader wedding/venue industry landscape.

4. VENUE IMPACT
Write 1 paragraph on specific implications for venue owners - how does this affect their business?

5. ACTIONABLE INSIGHTS
Provide 2-3 bullet points on what venues should do or consider based on this news.

6. SOURCE
{news_topic.get('url', 'N/A')} ({news_topic.get('publisher', 'Unknown')})

Target: 400-500 words total. Be factual, cite specifics from the summary, avoid speculation."""

            news_research = openai_client.generate_content(
                prompt=news_research_prompt,
                model="gpt-5.2",
                temperature=0.3,
                max_tokens=1500
            )
            research_results['news'] = news_research['content']
            print(f"    NEWS research: {len(news_research['content'].split())} words")

        # Research TIP article (Half-Page ~200-250 words)
        if tip_topic:
            safe_print(f"  - Researching TIP: {tip_topic.get('title', 'Unknown')}")
            tip_research_prompt = f"""You are a senior industry analyst. Produce a half-page briefing (~200-250 words) for newsletter writers.

Article: {tip_topic.get('title', 'Unknown')}
Source: {tip_topic.get('url', 'N/A')}
Initial Summary: {tip_topic.get('description', '')}
Additional Context: {tip_topic.get('so_what', '')}

Produce a structured briefing with these sections:

1. CORE ADVICE
Write 1-2 sentences summarizing the main tip/advice.

2. SUPPORTING EVIDENCE
Provide bullet points explaining why this works - include any data or examples.

3. IMPLEMENTATION STEPS
Provide 2-3 actionable bullets on how venues can apply this tip immediately.

4. SOURCE
{tip_topic.get('url', 'N/A')} ({tip_topic.get('publisher', 'Unknown')})

Target: 200-250 words total. Be practical and actionable."""

            tip_research = openai_client.generate_content(
                prompt=tip_research_prompt,
                model="gpt-5.2",
                temperature=0.3,
                max_tokens=800
            )
            research_results['tip'] = tip_research['content']
            print(f"    TIP research: {len(tip_research['content'].split())} words")

        # Research TREND article (Half-Page ~200-250 words)
        if trend_topic:
            safe_print(f"  - Researching TREND: {trend_topic.get('title', 'Unknown')}")
            trend_research_prompt = f"""You are a senior industry analyst. Produce a half-page briefing (~200-250 words) for newsletter writers.

Article: {trend_topic.get('title', 'Unknown')}
Source: {trend_topic.get('url', 'N/A')}
Initial Summary: {trend_topic.get('description', '')}
Additional Context: {trend_topic.get('so_what', '')}

Produce a structured briefing with these sections:

1. TREND OVERVIEW
Write 1-2 sentences describing what this trend is and why it's emerging now.

2. MARKET SIGNALS
Provide bullet points with data/examples proving this is a real trend - statistics, industry examples, expert quotes.

3. VENUE OPPORTUNITY
Provide 2-3 actionable bullets on how venues can capitalize on this trend.

4. SOURCE
{trend_topic.get('url', 'N/A')} ({trend_topic.get('publisher', 'Unknown')})

Target: 200-250 words total. Focus on opportunity and inspiration."""

            trend_research = openai_client.generate_content(
                prompt=trend_research_prompt,
                model="gpt-5.2",
                temperature=0.3,
                max_tokens=800
            )
            research_results['trend'] = trend_research['content']
            print(f"    TREND research: {len(trend_research['content'].split())} words")

        print(f"[API] Research complete")

        return jsonify({
            'success': True,
            'research': research_results,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] Research failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """
    Generate newsletter content using Claude Opus 4.5.
    Accepts pre-researched summaries from /api/research-articles, or raw topics (legacy).
    """
    try:
        data = request.json
        month = data.get('month', 'january')

        # Check if we have research summaries (new flow) or raw topics (legacy flow)
        research = data.get('research')

        if research:
            # NEW FLOW: Use research summaries with Opus 4.5
            print(f"\n[API] Writing content for {month} using Claude Opus 4.5...")

            if not claude_client:
                raise ValueError("Claude client not available for writing")

            sections = {}

            # Write NEWS section from research
            if research.get('news'):
                safe_print(f"  - Writing NEWS section...")
                # Get section-specific style guide (includes NEWS structure from config)
                news_style_guide = get_style_guide_for_prompt('news')

                news_prompt = f"""You are the copywriter for Venue Voice, a professional newsletter for wedding venue owners.

## RESEARCH BRIEFING
{research['news']}

{news_style_guide}

## OUTPUT REQUIREMENTS
Section: NEWS (Full Article)
Total word count: 250-300 words
Structure: Three clearly labeled subsections

**The Short Version:** (1-2 sentences, ~25 words)
A punchy summary of the key news.

**What's Happening:** (~150 words)
The main story with context, statistics, and industry perspective. Include specific data points and examples.

**Why It Matters for Venues:** (~80 words)
Direct, actionable implications for venue owners. What should they do or consider?

## EXAMPLE OUTPUT
*The Short Version:* Sustainability has shifted from a nice-to-have perk to a must-have standard, with couples actively seeking eco-conscious venues for their celebrations.

*What's Happening:* The wedding industry is experiencing a green revolution. According to a recent survey, 78% of engaged couples now consider a venue's environmental practices when making their booking decision — up from just 34% five years ago. This isn't limited to recycling bins and LED lighting. Couples want to see solar panels, composting programs, locally sourced catering options, and partnerships with sustainable vendors. Major venue networks report that properties with verified green certifications see 23% higher inquiry rates than comparable venues without credentials. The trend spans all price points, from rustic barn weddings to luxury estates.

*Why It Matters for Venues:* Start documenting your existing eco-friendly practices — you likely have more than you realize. Consider pursuing certification through programs like Green Wedding Alliance or local sustainability councils. Even small changes, like switching to cloth napkins or partnering with a local florist, can become powerful marketing differentiators that attract environmentally conscious couples.

Write the NEWS section now. Output the three subsections with bold labels (*The Short Version:*, *What's Happening:*, *Why It Matters for Venues:*). Use plain text with line breaks between sections."""

                news_result = claude_client.generate_content(
                    prompt=news_prompt,
                    model="claude-opus-4-5-20251101",
                    temperature=0.4,
                    max_tokens=600
                )

                # Format as HTML with proper styling
                news_text = news_result['content'].strip()

                # Convert markdown-style formatting to HTML

                # Replace *text:* with <strong>text:</strong> for section labels (bold)
                news_text = re.sub(r'\*([^*]+):\*', r'<strong>\1:</strong>', news_text)

                # Split into paragraphs and wrap each
                paragraphs = [p.strip() for p in news_text.split('\n\n') if p.strip()]
                formatted_paragraphs = []
                for p in paragraphs:
                    # Handle single newlines within paragraphs
                    p = p.replace('\n', ' ')
                    formatted_paragraphs.append(f'<p style="margin: 0 0 16px 0; font-family: \'Gilroy\', Trebuchet MS, sans-serif; font-size: 15px; color: #555555; line-height: 1.7;" class="dark-mode-secondary">{p}</p>')

                sections['news'] = '\n'.join(formatted_paragraphs)

            # Write TIP section from research (BRITECO INSIGHT)
            if research.get('tip'):
                safe_print(f"  - Writing TIP section...")

                # Generate title and subtitle together
                tip_title_prompt = f"""Based on this research briefing, create:
1. A 4-6 word TITLE in Title Case (action-oriented)
2. A 6-10 word SUBTITLE (italicized tagline that summarizes the benefit)

{research['tip']}

## EXAMPLE
TITLE: Host High-Impact Showcases
SUBTITLE: Turn open days into your #1 booking engine.

Output format (exactly two lines):
TITLE: [your title]
SUBTITLE: [your subtitle]"""

                tip_title_result = claude_client.generate_content(
                    prompt=tip_title_prompt,
                    model="claude-opus-4-5-20251101",
                    temperature=0.4,
                    max_tokens=60
                )

                # Parse title and subtitle
                title_response = tip_title_result['content'].strip()
                tip_title = ""
                tip_subtitle = ""
                for line in title_response.split('\n'):
                    if line.startswith('TITLE:'):
                        tip_title = line.replace('TITLE:', '').strip().replace('"', '').replace("'", "")
                    elif line.startswith('SUBTITLE:'):
                        tip_subtitle = line.replace('SUBTITLE:', '').strip().replace('"', '').replace("'", "")

                if not tip_title:
                    tip_title = "Expert Venue Advice"
                if not tip_subtitle:
                    tip_subtitle = "Actionable insights for your venue."

                # Generate body content with section-specific style guide
                tip_style_guide = get_style_guide_for_prompt('tip')

                tip_prompt = f"""You are the copywriter for Venue Voice newsletter's BRITECO INSIGHT section.

## RESEARCH BRIEFING
{research['tip']}

{tip_style_guide}

## OUTPUT REQUIREMENTS
Section: BRITECO INSIGHT (practical advice for venue owners)
Word count: 80-100 words (ONE paragraph)
Tone: Helpful, expert, actionable
Purpose: Provide specific, implementable advice that venue owners can use immediately

## EXAMPLE OUTPUT
Stop treating open houses as passive property tours. The most successful venues create immersive mini-experiences: tasting stations with signature cocktails, ambient lighting that matches evening reception vibes, and guest books where visitors can note their favorite features. Consider partnering with a local florist to stage tablescapes or hiring a DJ for an hour to demonstrate sound quality. Capture email addresses at entry and follow up within 48 hours with a personalized video message referencing their visit.

Write the TIP body paragraph now. Output ONLY the paragraph text, no title or formatting."""

                tip_result = claude_client.generate_content(
                    prompt=tip_prompt,
                    model="claude-opus-4-5-20251101",
                    temperature=0.4,
                    max_tokens=200
                )

                tip_text = tip_result['content'].strip()

                # Build HTML - subtitle separate, content without asterisks
                sections['tip'] = f'''<p style="margin: 0 0 14px 0; font-family: 'Gilroy', Trebuchet MS, sans-serif; font-size: 14px; color: #555555; line-height: 1.6;" class="dark-mode-secondary">{tip_text}</p>'''
                sections['tip_title'] = tip_title
                sections['tip_subtitle'] = f'''<p style="margin: 0 0 12px 0; font-family: 'Gilroy', Trebuchet MS, sans-serif; font-size: 13px; font-style: italic; color: #008181; line-height: 1.4;">{tip_subtitle}</p>'''

            # Write TREND section from research (TREND ALERT)
            if research.get('trend'):
                safe_print(f"  - Writing TREND section...")

                # Generate title and subtitle together
                trend_title_prompt = f"""Based on this research briefing, create:
1. A 4-6 word TITLE in Title Case (trend-focused, evocative)
2. A 6-10 word SUBTITLE (italicized tagline capturing the essence)

{research['trend']}

## EXAMPLE
TITLE: Cinematic 2026 Wedding Moments
SUBTITLE: Moody color, immersive vibes, highly intentional everything.

Output format (exactly two lines):
TITLE: [your title]
SUBTITLE: [your subtitle]"""

                trend_title_result = claude_client.generate_content(
                    prompt=trend_title_prompt,
                    model="claude-opus-4-5-20251101",
                    temperature=0.4,
                    max_tokens=60
                )

                # Parse title and subtitle
                title_response = trend_title_result['content'].strip()
                trend_title = ""
                trend_subtitle = ""
                for line in title_response.split('\n'):
                    if line.startswith('TITLE:'):
                        trend_title = line.replace('TITLE:', '').strip().replace('"', '').replace("'", "")
                    elif line.startswith('SUBTITLE:'):
                        trend_subtitle = line.replace('SUBTITLE:', '').strip().replace('"', '').replace("'", "")

                if not trend_title:
                    trend_title = "Emerging Wedding Trends"
                if not trend_subtitle:
                    trend_subtitle = "What couples are asking for now."

                # Generate body content with section-specific style guide
                trend_style_guide = get_style_guide_for_prompt('trend')

                trend_prompt = f"""You are the copywriter for Venue Voice newsletter's TREND ALERT section.

## RESEARCH BRIEFING
{research['trend']}

{trend_style_guide}

## OUTPUT REQUIREMENTS
Section: TREND ALERT (emerging wedding/event trends)
Word count: 60-80 words (ONE paragraph)
Tone: Trend-forward, inspiring, slightly editorial
Purpose: Help venue owners understand what's coming and how to prepare

## EXAMPLE OUTPUT
The age of the Pinterest-perfect wedding is fading. In its place, couples are demanding cinematic experiences — think moody lighting, dramatic entrances, and reception moments designed for film rather than still photography. Venues that offer fog machines, intelligent lighting systems, and dedicated "first look" spaces are winning bookings. Consider partnering with videographers who can showcase your space's most dramatic angles in promotional content.

Write the TREND body paragraph now. Output ONLY the paragraph text, no title or formatting."""

                trend_result = claude_client.generate_content(
                    prompt=trend_prompt,
                    model="claude-opus-4-5-20251101",
                    temperature=0.4,
                    max_tokens=180
                )

                trend_text = trend_result['content'].strip()

                # Build HTML - subtitle separate, content without asterisks
                sections['trend'] = f'''<p style="margin: 0 0 14px 0; font-family: 'Gilroy', Trebuchet MS, sans-serif; font-size: 14px; color: #ffffff; line-height: 1.6;">{trend_text}</p>'''
                sections['trend_title'] = trend_title
                sections['trend_subtitle'] = f'''<p style="margin: 0 0 12px 0; font-family: 'Gilroy', Trebuchet MS, sans-serif; font-size: 13px; font-style: italic; color: #272d3f; line-height: 1.4;">{trend_subtitle}</p>'''

            print(f"[API] Content written successfully with Opus 4.5")

            return jsonify({
                'success': True,
                'content': sections,
                'generated_at': datetime.now().isoformat()
            })

        # LEGACY FLOW: Direct topic-to-content (for backwards compatibility)
        news_topic = data.get('news_topic')
        tip_topic = data.get('tip_topic')
        trend_topic = data.get('trend_topic')
        ai_model = data.get('ai_model', 'chatgpt')

        # Select the AI client based on user choice
        if ai_model == 'claude' and claude_client:
            ai_client = claude_client
            model_name = "Claude (Sonnet 4.5)"
        elif ai_model == 'gemini':
            ai_client = openai_client
            model_name = "ChatGPT (GPT-4o) - Gemini text support coming soon"
        else:
            ai_client = openai_client
            model_name = "ChatGPT (GPT-4o)"

        print(f"\n[API] Generating content for {month} using {model_name} (legacy flow)...")

        # Helper function to parse JSON from AI response (handles markdown wrapping)
        def parse_json_response(content):
            """Parse JSON from AI response, stripping markdown code blocks if present"""
            try:
                # Remove markdown code blocks if present
                cleaned = content.strip()
                if cleaned.startswith('```'):
                    # Remove opening ```json or ```
                    cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned
                    # Remove closing ```
                    if cleaned.endswith('```'):
                        cleaned = cleaned.rsplit('```', 1)[0]
                cleaned = cleaned.strip()
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                print(f"    Failed to parse JSON: {e}")
                print(f"    Content preview: {content[:200]}")
                return {'raw': content}

        # Generate each section
        sections = {}

        # News section
        if news_topic:
            safe_print(f"  - Generating news: {news_topic['title']}")
            news_prompt = f"""Write 2-3 sentences about: {news_topic['title']}

30-35 words ONLY. NO statistics.

<p>Brief explanation here.</p>"""

            news_result = ai_client.generate_content(
                prompt=news_prompt,
                temperature=0.1,
                max_tokens=80
            )

            # Clean up and truncate
            news_content = news_result['content'].strip()
            if news_content.startswith('```'):
                news_content = news_content.split('\n', 1)[1] if '\n' in news_content else news_content
                if news_content.endswith('```'):
                    news_content = news_content.rsplit('```', 1)[0]
            news_content = news_content.strip()

            # Force truncate to 35 words if needed
            if '<p>' in news_content:
                match = re.search(r'<p>(.*?)</p>', news_content, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    words = text.split()
                    if len(words) > 35:
                        text = ' '.join(words[:35]) + '.'
                    # Add inline styling for news content with proper bottom margin
                    news_content = f'<p style="margin: 0 0 16px 0; font-family: \'Gilroy\', Trebuchet MS, sans-serif; font-size: 15px; color: #555555; line-height: 1.7;" class="dark-mode-secondary">{text}</p>'

            sections['news'] = news_content

        # Tip section
        if tip_topic:
            safe_print(f"  - Generating tip: {tip_topic['title']}")

            # Generate short summary title (6-8 words)
            tip_title_prompt = f"""Summarize in 4-6 words: {tip_topic['title']}"""
            tip_title_result = ai_client.generate_content(
                prompt=tip_title_prompt,
                temperature=0.1,
                max_tokens=20
            )
            tip_title = tip_title_result['content'].strip().replace('"', '').replace("'", "")
            words = tip_title.split()
            if len(words) > 6:
                tip_title = ' '.join(words[:6])

            # Generate content
            tip_prompt = f"""Write ONE sentence about: {tip_topic['title']}

10-12 words ONLY.

<p>Short tip sentence here.</p>"""

            tip_result = ai_client.generate_content(
                prompt=tip_prompt,
                temperature=0.1,
                max_tokens=30
            )

            # Clean up and truncate
            tip_content = tip_result['content'].strip()
            if tip_content.startswith('```'):
                tip_content = tip_content.split('\n', 1)[1] if '\n' in tip_content else tip_content
                if tip_content.endswith('```'):
                    tip_content = tip_content.rsplit('```', 1)[0]
            tip_content = tip_content.strip()

            # Force truncate to 12 words if needed
            if '<p>' in tip_content:
                match = re.search(r'<p>(.*?)</p>', tip_content, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    words = text.split()
                    if len(words) > 12:
                        text = ' '.join(words[:12]) + '.'
                    # Add inline styling for tip content with proper spacing
                    tip_content = f'<p style="margin: 0 0 14px 0; font-family: \'Gilroy\', Trebuchet MS, sans-serif; font-size: 14px; color: #555555; line-height: 1.6;" class="dark-mode-secondary">{text}</p>'

            sections['tip'] = tip_content
            sections['tip_title'] = tip_title

        # Trend section
        if trend_topic:
            safe_print(f"  - Generating trend: {trend_topic['title']}")

            # Generate short summary title (6-8 words)
            trend_title_prompt = f"""Summarize in 4-6 words: {trend_topic['title']}"""
            trend_title_result = ai_client.generate_content(
                prompt=trend_title_prompt,
                temperature=0.1,
                max_tokens=20
            )
            trend_title = trend_title_result['content'].strip().replace('"', '').replace("'", "")
            words = trend_title.split()
            if len(words) > 6:
                trend_title = ' '.join(words[:6])

            # Generate content
            trend_prompt = f"""Write ONE sentence about: {trend_topic['title']}

10-12 words ONLY.

<p>Short trend sentence here.</p>"""

            trend_result = ai_client.generate_content(
                prompt=trend_prompt,
                temperature=0.1,
                max_tokens=30
            )

            # Clean up and truncate
            trend_content = trend_result['content'].strip()
            if trend_content.startswith('```'):
                trend_content = trend_content.split('\n', 1)[1] if '\n' in trend_content else trend_content
                if trend_content.endswith('```'):
                    trend_content = trend_content.rsplit('```', 1)[0]
            trend_content = trend_content.strip()

            # Force truncate to 12 words if needed
            if '<p>' in trend_content:
                match = re.search(r'<p>(.*?)</p>', trend_content, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    words = text.split()
                    if len(words) > 12:
                        text = ' '.join(words[:12]) + '.'
                    # Add inline styling for trend content with proper spacing, white text for dark background
                    trend_content = f'<p style="margin: 0 0 14px 0; font-family: \'Gilroy\', Trebuchet MS, sans-serif; font-size: 14px; color: #ffffff; line-height: 1.6;">{text}</p>'

            sections['trend'] = trend_content
            sections['trend_title'] = trend_title

        print(f"[API] Content generated successfully")

        return jsonify({
            'success': True,
            'content': sections,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-image-prompts', methods=['POST'])
def generate_image_prompts():
    """Generate image prompts for newsletter sections (without generating images yet)"""
    try:
        data = request.json
        sections = data.get('sections', {})
        month = data.get('month', 'january')

        # Determine season from month
        month_to_season = {
            'january': 'winter', 'february': 'winter', 'december': 'winter',
            'march': 'spring', 'april': 'spring', 'may': 'spring',
            'june': 'summer', 'july': 'summer', 'august': 'summer',
            'september': 'fall', 'october': 'fall', 'november': 'fall'
        }
        season = month_to_season.get(month.lower(), 'spring')

        print(f"\n[API] Generating image prompts for {len(sections)} sections (month: {month}, season: {season})...")

        prompts = {}

        # Generate prompt for each section using ChatGPT
        for section_name, section_data in sections.items():
            print(f"  - Creating image prompt for {section_name}")

            # Get article title and context
            title = section_data.get('title', '')
            content_raw = section_data.get('content', '')

            # Debug: Show what we received
            print(f"    [DEBUG] Raw content type: {type(content_raw)}")
            print(f"    [DEBUG] Raw content preview: {str(content_raw)[:200]}")

            # Extract meaningful text from content object
            content = ''
            if isinstance(content_raw, dict):
                # News article structure
                if 'short_version' in content_raw:
                    content = f"{content_raw.get('short_version', '')} {content_raw.get('whats_happening', '')} {content_raw.get('why_matters', '')}"
                # Tip structure
                elif 'intro' in content_raw:
                    steps = ' '.join(content_raw.get('steps', []))
                    content = f"{content_raw.get('intro', '')} {steps} {content_raw.get('pro_tip', '')}"
                # Trend structure
                elif 'overview' in content_raw:
                    examples = ' '.join(content_raw.get('examples', []))
                    content = f"{content_raw.get('overview', '')} {examples} {content_raw.get('opportunity', '')}"
                else:
                    content = str(content_raw)[:500]
            elif isinstance(content_raw, str):
                content = content_raw[:500]
            else:
                content = str(content_raw)[:500]

            safe_print(f"    Title: {title[:80]}")
            print(f"    Extracted content length: {len(content)} chars")
            safe_print(f"    Extracted content (first 150 chars): {content[:150]}")

            if not content or len(content.strip()) < 10:
                print(f"    [WARNING] Content is empty or too short! Using fallback prompt.")

            # Use Claude to generate an optimized image prompt based on best practices
            # Add seasonal context
            seasonal_details = {
                'winter': 'winter elements like pine, candles, warm lighting, cozy atmosphere, silver/gold accents',
                'spring': 'spring elements like fresh flowers, pastel colors, natural light, blooming details, soft pastels',
                'summer': 'summer elements like bright natural light, outdoor settings, lush greenery, vibrant colors',
                'fall': 'fall elements like autumn leaves, warm tones, pumpkins, rustic details, golden hour lighting'
            }
            seasonal_hint = seasonal_details.get(season, '')

            prompt_request = f"""Create a text-to-image prompt for Gemini that VISUALLY REPRESENTS this article's main topic.

Article Title: "{title}"
Article Content: "{content[:400]}..."
Season: {season.capitalize()}

CRITICAL: The image must VISUALLY show what the article is about. Examples:
- Article about "Virtual Tours" or "40% More Inquiries from Virtual Tours" → Show screens/tablets displaying venue tours, or 360-degree camera setup
- Article about "Video Marketing" or "1200% More Shares with Video" → Show video recording equipment, cameras on tripods, screens displaying video content
- Article about "Lighting" → Show dramatic venue lighting, chandeliers, uplighting
- Article about "Outdoor Venues" → Show outdoor ceremony/reception space
- Article about "Pricing" → Show elegant tiered packages display, pricing menu boards
- Article about "Sustainability" → Show eco-friendly venue details, greenery, natural elements

IMPORTANT: If the title contains statistics or percentages (like "40%", "70%", "1200%"), visually represent the technology or concept being measured through screens, cameras, displays, tablets, tech equipment, or elegant data visualizations.

YOUR TASK: Create a prompt that shows the SPECIFIC topic from "{title}" visually in a wedding venue context.

REQUIREMENTS:
- Subject: Must VISUALLY represent "{title[:60]}" - not just a generic venue!
- Setting: Wedding venue interior/exterior that relates to the article topic
- Style: Professional architectural/venue photography, magazine quality
- Season: Incorporate {season} elements ({seasonal_hint})
- Quality: High-end, luxury, well-lit, sharp detail
- NO: Text overlays, people's faces, generic spaces

Return ONLY the image generation prompt (under 35 words). Make it SPECIFIC to the article topic!"""

            # Use Claude for better prompt generation if available
            if claude_client:
                try:
                    print(f"    [CALLING CLAUDE] Sending prompt request to Claude...")
                    safe_print(f"    [DEBUG] Article title: {title}")
                    print(f"    [DEBUG] Content length: {len(content)} chars")
                    safe_print(f"    [DEBUG] Content preview: {content[:150]}...")

                    claude_response = claude_client.generate_content(
                        prompt=prompt_request,
                        max_tokens=100,
                        temperature=0.7
                    )
                    prompt = claude_response.get('content', '').strip().replace('"', '').replace("'", "")
                    safe_print(f"    [CLAUDE SUCCESS] Generated: {prompt}")
                except Exception as e:
                    print(f"    [CLAUDE FAILED] Using fallback: {e}")
                    # Fallback to a generic but themed prompt
                    section_styles = {
                        'news': 'modern wedding venue interior with elegant decor and natural lighting',
                        'tip': 'intimate wedding venue detail with personalized touches and warm atmosphere',
                        'trend': 'stylish seasonal wedding decor with trendy color palette and floral arrangements'
                    }
                    prompt = section_styles.get(section_name, f"Professional wedding venue related to {title[:40]}")
            else:
                print(f"    [WARNING] Claude not available, using fallback prompt")
                # Fallback to a generic but themed prompt
                section_styles = {
                    'news': 'modern wedding venue interior with elegant decor and natural lighting',
                    'tip': 'intimate wedding venue detail with personalized touches and warm atmosphere',
                    'trend': 'stylish seasonal wedding decor with trendy color palette and floral arrangements'
                }
                prompt = section_styles.get(section_name, f"Professional wedding venue related to {title[:40]}")

            prompts[section_name] = prompt

        print(f"[API] Generated {len(prompts)} image prompts")

        return jsonify({
            'success': True,
            'prompts': prompts
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-subject-options', methods=['POST'])
def generate_subject_options():
    """Generate 5 subject line and 5 preheader options using Claude"""
    try:
        data = request.json
        content = data.get('content', {})
        tone = data.get('tone', 'professional')  # Default to professional

        print(f"\n[API] Generating subject line and preheader options (tone: {tone})...")

        # Build context from newsletter content
        month = content.get('month', '')
        news = content.get('news', {})
        tip = content.get('tip', {})
        trend = content.get('trend', {})

        # Determine season from month for seasonal context
        month_to_season = {
            'january': 'winter', 'february': 'winter', 'december': 'winter',
            'march': 'spring', 'april': 'spring', 'may': 'spring',
            'june': 'summer', 'july': 'summer', 'august': 'summer',
            'september': 'fall', 'october': 'fall', 'november': 'fall'
        }
        season = month_to_season.get(month.lower(), 'spring')

        # Create summary of newsletter content
        content_summary = f"""Newsletter for {month.capitalize()} ({season.capitalize()} Season):

NEWS SECTION:
Title: {news.get('title', '')}
Content: {str(news.get('content', ''))[:300]}...

TIP SECTION:
Title: {tip.get('title', '')}
Content: {str(tip.get('content', ''))[:300]}...

TREND SECTION:
Title: {trend.get('title', '')}
Content: {str(trend.get('content', ''))[:300]}..."""

        # Define tone instructions
        tone_instructions = {
            'professional': 'Use professional, informative language. Focus on data and insights. Formal but approachable.',
            'friendly': 'Use warm, conversational language. Address the reader directly. Sound like a helpful colleague.',
            'urgent': 'Create a sense of urgency and FOMO. Use action-oriented verbs. Emphasize time-sensitive value.',
            'playful': 'Use fun, lighthearted language. Include wordplay or puns where appropriate. Keep it upbeat.',
            'exclusive': 'Create a sense of exclusivity and premium value. Use sophisticated language. Make it feel special.'
        }

        tone_instruction = tone_instructions.get(tone, tone_instructions['professional'])

        # Generate subject lines using Claude with tone
        subject_prompt = f"""Based on this wedding venue newsletter content, generate 5 compelling email subject lines.

{content_summary}

TONE INSTRUCTION: {tone_instruction}

Requirements:
- Each subject line should be 40-60 characters
- Focus on the most interesting or valuable content
- Match the specified tone consistently
- Make it relevant to wedding venue owners/managers
- Incorporate {season} seasonality where appropriate (e.g., mention the season, seasonal trends, or time-sensitive relevance)
- Avoid spam trigger words

Return ONLY 5 subject lines, numbered 1-5, one per line. No other text."""

        print(f"[API] Calling Claude to generate subject lines...")
        subject_response = claude_client.generate_content(
            prompt=subject_prompt,
            max_tokens=200,
            temperature=0.8
        )

        # Parse subject lines
        subject_lines = []
        for line in subject_response.get('content', '').strip().split('\n'):
            cleaned = line.strip()
            # Remove numbering
            if cleaned and (cleaned[0].isdigit() or cleaned.startswith('-')):
                cleaned = cleaned.split('.', 1)[-1].strip()
                cleaned = cleaned.lstrip('- ')
            if cleaned:
                subject_lines.append(cleaned)

        # Ensure we have exactly 5
        subject_lines = subject_lines[:5]
        while len(subject_lines) < 5:
            subject_lines.append(f"Wedding Venue Insights: {month.capitalize()} Newsletter")

        print(f"[API] Generated {len(subject_lines)} subject lines")
        for idx, subject in enumerate(subject_lines, 1):
            safe_print(f"  {idx}. {subject}")

        # Generate preheaders using Claude with same tone
        preheader_prompt = f"""Based on this wedding venue newsletter content, generate 5 compelling email preheaders.

{content_summary}

TONE INSTRUCTION: {tone_instruction}

Requirements:
- Each preheader should be 40-80 characters
- Complement (not repeat) the subject line
- Tease the newsletter content
- Provide additional value or context
- Create interest to open the email
- Match the specified tone consistently

Return ONLY 5 preheaders, numbered 1-5, one per line. No other text."""

        print(f"[API] Calling Claude to generate preheaders...")
        preheader_response = claude_client.generate_content(
            prompt=preheader_prompt,
            max_tokens=200,
            temperature=0.8
        )

        # Parse preheaders
        preheaders = []
        for line in preheader_response.get('content', '').strip().split('\n'):
            cleaned = line.strip()
            # Remove numbering
            if cleaned and (cleaned[0].isdigit() or cleaned.startswith('-')):
                cleaned = cleaned.split('.', 1)[-1].strip()
                cleaned = cleaned.lstrip('- ')
            if cleaned:
                preheaders.append(cleaned)

        # Ensure we have exactly 5
        preheaders = preheaders[:5]
        while len(preheaders) < 5:
            preheaders.append(f"Your monthly wedding industry insights inside")

        print(f"[API] Generated {len(preheaders)} preheaders")
        for idx, preheader in enumerate(preheaders, 1):
            safe_print(f"  {idx}. {preheader}")

        return jsonify({
            'success': True,
            'subject_lines': subject_lines,
            'preheaders': preheaders
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-images', methods=['POST'])
def generate_images():
    """Generate images for newsletter sections using provided or auto-generated prompts"""
    try:
        data = request.json
        sections = data.get('sections', {})
        prompts = data.get('prompts', {})  # Pre-generated or user-edited prompts

        print(f"\n[API] Generating images with Nano Banana (Gemini)...")
        print(f"[API] Received {len(prompts)} prompts")

        images = {}

        # Generate image for each prompt
        for section_name, prompt in prompts.items():
            safe_print(f"  [{section_name.upper()}] Prompt: {prompt}")

            # Determine aspect ratio based on section
            # News: 480x260px (full width landscape)
            # Tip: 432x130px (wide banner)
            # Trend: 432x130px (wide banner)
            if section_name == 'news':
                aspect_ratio = "16:9"  # Landscape for full-width news image
            else:
                aspect_ratio = "16:9"  # Wide landscape for banner-style tip/trend images

            # Generate with Gemini 3 Pro Image Preview
            print(f"  [{section_name.upper()}] Calling Gemini 3 Pro Image...")
            image_result = gemini_client.generate_image(
                prompt=prompt,
                model="gemini-3-pro-image-preview",
                aspect_ratio=aspect_ratio,
                image_size="1K"
            )

            # Get the base64 image data
            image_data = image_result.get('image_data', '')

            # Resize image to exact newsletter dimensions
            if image_data:
                try:
                    import base64
                    from PIL import Image
                    from io import BytesIO

                    # Decode base64 to PIL Image
                    image_bytes = base64.b64decode(image_data)
                    pil_image = Image.open(BytesIO(image_bytes))

                    # Determine target size based on section
                    if section_name == 'news':
                        # News: 480px wide, aspect ratio for new template = 480x260
                        target_width = 480
                        target_height = 260
                    else:
                        # Tip/Trend: 432px wide, 130px tall (landscape banner)
                        target_width = 432
                        target_height = 130

                    print(f"  [{section_name.upper()}] Resizing from {pil_image.size} to {target_width}x{target_height}...")

                    # Calculate aspect ratios
                    img_aspect = pil_image.width / pil_image.height
                    target_aspect = target_width / target_height

                    # Resize maintaining aspect ratio, then crop to exact size
                    if img_aspect > target_aspect:
                        # Image is wider - resize based on height, then crop width
                        new_height = target_height
                        new_width = int(target_height * img_aspect)
                    else:
                        # Image is taller - resize based on width, then crop height
                        new_width = target_width
                        new_height = int(target_width / img_aspect)

                    # Resize maintaining aspect ratio
                    resized_temp = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Center crop to exact target dimensions
                    left = (new_width - target_width) // 2
                    top = (new_height - target_height) // 2
                    right = left + target_width
                    bottom = top + target_height

                    resized_image = resized_temp.crop((left, top, right, bottom))

                    # Convert back to base64
                    buffer = BytesIO()
                    resized_image.save(buffer, format='PNG', optimize=True)
                    resized_bytes = buffer.getvalue()
                    image_data = base64.b64encode(resized_bytes).decode('utf-8')

                    print(f"  [{section_name.upper()}] Resized successfully to {target_width}x{target_height}")

                except Exception as resize_error:
                    print(f"  [{section_name.upper()}] Resize failed, using original: {resize_error}")

            # Convert to data URL for frontend display
            image_url = f"data:image/png;base64,{image_data}" if image_data else ''

            images[section_name] = image_url
            print(f"  [{section_name.upper()}] SUCCESS - Image generated and sized ({len(image_data)} bytes)")

        print(f"[API] Generated {len(images)} images")

        return jsonify({
            'success': True,
            'images': images,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# DISABLED: Search memes endpoint - not currently in use
# Kept for potential future use
# @app.route('/api/search-memes', methods=['POST'])
# def search_memes():
#     """Search web for wedding memes using Google Custom Search"""
#     try:
#         data = request.json
#         month = data.get('month', '')
#
#         print(f"\n[API] Searching for wedding memes for {month}...")
#
#         # Month-specific search queries
#         month_queries = {
#             'january': 'wedding planning new year funny meme',
#             'february': 'wedding valentines day funny meme',
#             'march': 'spring wedding season funny meme',
#             'april': 'wedding rain funny meme',
#             'may': 'wedding season chaos funny meme',
#             'june': 'peak wedding season stress funny meme',
#             'july': 'summer outdoor wedding funny meme',
#             'august': 'late summer wedding funny meme',
#             'september': 'fall wedding funny meme',
#             'october': 'halloween wedding funny meme',
#             'november': 'thanksgiving wedding funny meme',
#             'december': 'holiday wedding funny meme'
#         }
#
#         search_query = month_queries.get(month.lower(), 'wedding venue funny meme')
#
#         # Use Brave Search API for image search
#         try:
#             import requests as req
#             brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY', '')
#
#             if brave_api_key:
#                 # Brave Image Search API
#                 brave_url = 'https://api.search.brave.com/res/v1/images/search'
#                 headers = {
#                     'Accept': 'application/json',
#                     'Accept-Encoding': 'gzip',
#                     'X-Subscription-Token': brave_api_key
#                 }
#                 params = {
#                     'q': search_query,
#                     'count': 10,
#                     'safesearch': 'moderate'
#                 }
#
#                 response = req.get(brave_url, headers=headers, params=params, timeout=10)
#
#                 if response.status_code == 200:
#                     results = response.json()
#                     images = []
#
#                     for result in results.get('results', [])[:8]:  # Limit to 8 results
#                         images.append({
#                             'url': result.get('properties', {}).get('url', result.get('url', '')),
#                             'thumbnail': result.get('thumbnail', {}).get('src', result.get('url', '')),
#                             'title': result.get('title', 'Wedding Meme')
#                         })
#
#                     print(f"[API] Found {len(images)} memes from Brave Search")
#
#                     return jsonify({
#                         'success': True,
#                         'images': images,
#                         'search_query': search_query
#                     })
#                 else:
#                     print(f"[API WARNING] Brave Search failed: {response.status_code}")
#             else:
#                 print(f"[API WARNING] Brave API key not configured")
#         except Exception as search_error:
#             print(f"[API WARNING] Image search failed: {search_error}")
#
#         # Fallback: Suggest user upload their own or use generated meme
#         print(f"[API] Returning fallback message")
#
#         return jsonify({
#             'success': False,
#             'error': 'Image search unavailable. Please upload your own meme or use the generated one.',
#             'images': []
#         })
#
#     except Exception as e:
#         print(f"[API ERROR] {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-meme-prompt', methods=['POST'])
def generate_meme_prompt():
    """Generate meme prompt based on newsletter content using Claude"""
    try:
        data = request.json
        sections = data.get('sections', {})
        month = data.get('month', 'january')

        print(f"\n[API] Generating meme prompt based on newsletter content for {month}...")

        # Extract content from sections
        news_content = sections.get('news', {}).get('content', '')
        tip_content = sections.get('tip', {}).get('content', '')
        trend_content = sections.get('trend', {}).get('content', '')

        # Create a summary of newsletter topics
        newsletter_summary = f"""Newsletter Content Summary:
- News: {news_content[:200]}...
- Tip: {tip_content[:200]}...
- Trend: {trend_content[:200]}..."""

        # Use Claude to generate meme concept
        meme_prompt_request = f"""Based on this wedding venue newsletter content, create a funny, relatable meme concept.

{newsletter_summary}

Generate:
1. A visual scene description (15-25 words) - what the image should show
2. Top text (3-6 words, all caps) - the setup
3. Bottom text (3-8 words, all caps) - the punchline

The meme should:
- Be funny and relatable to wedding venue owners/managers
- Reference one of the newsletter topics in a humorous way
- Work in classic meme format (image with top/bottom text)
- Be shareable and make venue professionals laugh

Return ONLY in this exact JSON format:
{{"scene": "description here", "top": "TOP TEXT", "bottom": "BOTTOM TEXT"}}"""

        try:
            print("    Calling Claude API...")
            response = claude_client.generate_content(
                prompt=meme_prompt_request,
                max_tokens=150,
                temperature=0.9
            )

            print(f"    Claude raw response: {response}")

            import json
            content = response.get('content', '{}')
            print(f"    Claude content to parse: {content}")

            # Strip markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            print(f"    Cleaned content: {content}")

            meme_data = json.loads(content)
            scene = meme_data.get('scene', 'Wedding venue professional looking stressed during peak season')
            text_top = meme_data.get('top', 'WEDDING SEASON').upper()
            text_bottom = meme_data.get('bottom', "IT'S HAPPENING").upper()

            safe_print(f"    Generated meme concept:")
            safe_print(f"      Scene: {scene}")
            safe_print(f"      Top: {text_top}")
            safe_print(f"      Bottom: {text_bottom}")

        except Exception as e:
            print(f"    Claude failed, using fallback: {e}")
            # Fallback to generic wedding meme
            scene = "Wedding venue coordinator juggling multiple tasks during peak season"
            text_top = "WEDDING SEASON"
            text_bottom = "SEND HELP"

        return jsonify({
            'success': True,
            'scene': scene,
            'text_top': text_top,
            'text_bottom': text_bottom
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-meme', methods=['POST'])
def generate_meme():
    """Generate meme with Nano Banana using scene description and text overlay"""
    try:
        data = request.json
        month = data.get('month')
        custom_prompt = data.get('customPrompt') or data.get('prompt')  # Accept both parameter names

        # Get pre-generated text overlay (from meme prompt generation step)
        text_overlay_top = data.get('text_top', '').upper()
        text_overlay_bottom = data.get('text_bottom', '').upper()

        print(f"\n[API] Generating meme with Nano Banana for {month}...")
        safe_print(f"    Text overlay - Top: '{text_overlay_top}', Bottom: '{text_overlay_bottom}'")

        if custom_prompt:
            # Use user-provided prompt
            prompt = custom_prompt
            safe_print(f"    Using Claude-generated custom prompt:")
            safe_print(f"      {prompt}")
        else:
            # Generate prompt using ChatGPT
            month_themes = {
                'january': 'new year resolutions and wedding planning',
                'february': 'Valentine\'s Day and wedding season prep',
                'march': 'spring wedding season starting',
                'april': 'April showers and wedding planning',
                'may': 'May wedding season in full swing',
                'june': 'peak wedding season stress',
                'july': 'summer outdoor weddings',
                'august': 'late summer wedding fatigue',
                'september': 'fall wedding season',
                'october': 'Halloween and autumn weddings',
                'november': 'Thanksgiving and wedding planning',
                'december': 'holiday season weddings'
            }

            theme = month_themes.get(month.lower(), 'wedding venue business')

            # Use ChatGPT to create a fun meme prompt
            prompt_request = f"""Create a detailed text-to-image prompt (max 20 words) for a funny, relatable wedding industry meme about {theme}.

Requirements:
- Funny and relatable to wedding professionals
- Visual scene that tells a joke without needing text
- Professional but humorous
- Something wedding venue owners would laugh at and share
- No actual text/words in the image

Return ONLY the image prompt, nothing else."""

            try:
                gpt_response = openai_client.generate_content(
                    prompt=prompt_request,
                    max_tokens=50,
                    temperature=0.9  # Higher temp for more creative/funny results
                )
                prompt = gpt_response.get('content', '').strip().replace('"', '')
                safe_print(f"    Generated meme prompt: {prompt}")
            except Exception as e:
                print(f"    ChatGPT failed, using fallback: {e}")
                # Fallback to simple theme-based prompt
                prompt = f"Humorous wedding venue scene about {theme}, funny and relatable to wedding professionals"

        # If text overlay wasn't provided, generate fallback
        if not text_overlay_top and not text_overlay_bottom:
            text_overlay_top = "WEDDING SEASON"
            text_overlay_bottom = "IT'S HAPPENING"

        # Generate with Gemini 3 Pro Image Preview
        meme_result = gemini_client.generate_image(
            prompt=prompt,
            model="gemini-3-pro-image-preview",
            aspect_ratio="1:1",
            image_size="1K"
        )

        # Get the base64 image data
        image_data = meme_result.get('image_data', '')

        # Resize meme to newsletter dimensions (480x480 for 1:1 square)
        if image_data:
            try:
                import base64
                from PIL import Image
                from io import BytesIO

                # Decode base64 to PIL Image
                image_bytes = base64.b64decode(image_data)
                pil_image = Image.open(BytesIO(image_bytes))

                # Meme: 480px square (same width as news image)
                target_width = 480
                target_height = 480

                print(f"    [MEME] Resizing from {pil_image.size} to {target_width}x{target_height}...")

                # Use ImageOps.fit to crop/resize while maintaining aspect ratio (no squishing)
                from PIL import ImageOps
                resized_image = ImageOps.fit(pil_image, (target_width, target_height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

                # REMOVED: Text overlay is now handled by frontend HTML/CSS
                # Keeping this comment for reference - text_overlay_top and text_overlay_bottom
                # are returned to frontend for overlay positioning
                if False:  # Disabled - frontend handles text overlay
                    from PIL import ImageDraw, ImageFont
                    import textwrap

                    draw = ImageDraw.Draw(resized_image)

                    def draw_meme_text(text, position='top'):
                        """Draw text with automatic sizing and wrapping"""
                        max_width = target_width - 40  # 20px padding on each side

                        # Start with large font and reduce if needed
                        for font_size in range(48, 20, -2):
                            try:
                                font = ImageFont.truetype("impact.ttf", font_size)
                            except:
                                try:
                                    font = ImageFont.truetype("arialbd.ttf", font_size)
                                except:
                                    font = ImageFont.load_default()
                                    break

                            # Get single-line text width
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]

                            # If it fits on one line, use it
                            if text_width <= max_width:
                                # Single line
                                x = (target_width - text_width) / 2
                                y = 20 if position == 'top' else target_height - (bbox[3] - bbox[1]) - 20

                                draw.text((x, y), text, font=font, fill='white',
                                         stroke_width=3, stroke_fill='black')
                                return

                            # Try wrapping into 2 lines - try different split points
                            words = text.split()
                            if len(words) >= 2:
                                # Try splits from middle outward to find best fit
                                mid = len(words) // 2
                                for offset in [0, -1, 1, -2, 2]:
                                    split_point = mid + offset
                                    if split_point <= 0 or split_point >= len(words):
                                        continue

                                    line1 = ' '.join(words[:split_point])
                                    line2 = ' '.join(words[split_point:])

                                    bbox1 = draw.textbbox((0, 0), line1, font=font)
                                    bbox2 = draw.textbbox((0, 0), line2, font=font)

                                    width1 = bbox1[2] - bbox1[0]
                                    width2 = bbox2[2] - bbox2[0]

                                    if width1 <= max_width and width2 <= max_width:
                                        # Two lines fit!
                                        line_height = bbox1[3] - bbox1[1]

                                        x1 = (target_width - width1) / 2
                                        x2 = (target_width - width2) / 2

                                        if position == 'top':
                                            y1 = 15
                                            y2 = 15 + line_height + 5
                                        else:
                                            y2 = target_height - 15
                                            y1 = y2 - line_height - 5

                                        draw.text((x1, y1), line1, font=font, fill='white',
                                                 stroke_width=3, stroke_fill='black')
                                        draw.text((x2, y2), line2, font=font, fill='white',
                                                 stroke_width=3, stroke_fill='black')
                                        return

                        # Fallback: truncate text if still too long
                        print(f"    [MEME] Warning: Text too long, truncating: '{text}'")

                    # Add top text
                    if text_overlay_top:
                        draw_meme_text(text_overlay_top, 'top')
                        print(f"    [MEME] Added top text: '{text_overlay_top}'")

                    # Add bottom text
                    if text_overlay_bottom:
                        draw_meme_text(text_overlay_bottom, 'bottom')
                        print(f"    [MEME] Added bottom text: '{text_overlay_bottom}'")

                # Convert back to base64
                buffer = BytesIO()
                resized_image.save(buffer, format='PNG', optimize=True)
                resized_bytes = buffer.getvalue()
                image_data = base64.b64encode(resized_bytes).decode('utf-8')

                print(f"    [MEME] Resized successfully to {target_width}x{target_height}")

            except Exception as resize_error:
                print(f"    [MEME] Resize failed, using original: {resize_error}")

        # Convert to data URL for frontend display
        image_url = f"data:image/png;base64,{image_data}" if image_data else ''

        print(f"[API] Meme generated and resized successfully with text overlay")

        return jsonify({
            'success': True,
            'url': image_url,
            'prompt': prompt,  # Return the prompt so user can edit it
            'text_top': text_overlay_top,
            'text_bottom': text_overlay_bottom
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-meme', methods=['POST'])
def upload_meme():
    """Handle meme image upload with proper resizing to 480x480"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        print(f"[API] Processing uploaded meme: {file.filename}")

        import base64
        from PIL import Image, ImageOps
        from io import BytesIO

        # Read the file into PIL Image
        file_data = file.read()
        pil_image = Image.open(BytesIO(file_data))

        # Convert to RGB if necessary (for PNG with transparency or other modes)
        if pil_image.mode in ('RGBA', 'P', 'LA', 'L'):
            # Create white background for transparent images
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            if pil_image.mode == 'RGBA' or pil_image.mode == 'LA':
                background.paste(pil_image, mask=pil_image.split()[-1])
            else:
                background.paste(pil_image)
            pil_image = background

        # Resize to 480x480 using fit (crop to center, no squishing)
        target_size = (480, 480)
        print(f"    [UPLOAD] Resizing from {pil_image.size} to {target_size}...")
        resized_image = ImageOps.fit(pil_image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

        # Convert to base64
        buffer = BytesIO()
        resized_image.save(buffer, format='PNG', optimize=True)
        image_bytes = buffer.getvalue()
        image_data = base64.b64encode(image_bytes).decode('utf-8')

        # Create data URL
        image_url = f"data:image/png;base64,{image_data}"

        print(f"[API] Meme uploaded and resized successfully: {file.filename}")

        return jsonify({
            'success': True,
            'url': image_url,
            'filename': file.filename
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-meme-text', methods=['POST'])
def add_meme_text():
    """Add text overlay to meme image - burns text directly onto the image"""
    try:
        data = request.json
        image_url = data.get('image_url', '')  # Base64 data URL
        text_top = data.get('text_top', '').upper()
        text_bottom = data.get('text_bottom', '').upper()

        print(f"\n[API] Adding text overlay to meme...")
        print(f"    Top text: '{text_top}'")
        print(f"    Bottom text: '{text_bottom}'")

        if not image_url:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        if not text_top and not text_bottom:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        import base64
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO

        # Extract base64 data from data URL
        if ',' in image_url:
            image_data = image_url.split(',')[1]
        else:
            image_data = image_url

        # Decode and open image
        image_bytes = base64.b64decode(image_data)
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert to RGB if necessary (for PNG with transparency)
        if pil_image.mode in ('RGBA', 'P'):
            pil_image = pil_image.convert('RGB')

        draw = ImageDraw.Draw(pil_image)
        img_width, img_height = pil_image.size
        max_text_width = img_width - 40  # 20px padding each side

        def draw_meme_text(text, position='top'):
            """Draw text with automatic sizing and wrapping"""
            if not text:
                return

            # Try different font sizes, starting large
            for font_size in range(48, 18, -2):
                try:
                    # Try Impact font first (classic meme font)
                    font = ImageFont.truetype("impact.ttf", font_size)
                except:
                    try:
                        # Fallback to Arial Bold
                        font = ImageFont.truetype("arialbd.ttf", font_size)
                    except:
                        try:
                            # Try common Linux fonts
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                        except:
                            # Last resort: default font
                            font = ImageFont.load_default()
                            break

                # Get text bounding box
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Check if text fits on one line
                if text_width <= max_text_width:
                    # Center horizontally
                    x = (img_width - text_width) / 2
                    # Position vertically
                    if position == 'top':
                        y = 15
                    else:
                        y = img_height - text_height - 20

                    # Draw text with black outline (stroke) for visibility
                    draw.text((x, y), text, font=font, fill='white',
                             stroke_width=3, stroke_fill='black')
                    print(f"    [MEME] Drew {position} text at ({x}, {y}) with font size {font_size}")
                    return

                # Try wrapping into 2 lines
                words = text.split()
                if len(words) >= 2:
                    mid = len(words) // 2
                    for offset in [0, -1, 1, -2, 2]:
                        split_point = mid + offset
                        if split_point <= 0 or split_point >= len(words):
                            continue

                        line1 = ' '.join(words[:split_point])
                        line2 = ' '.join(words[split_point:])

                        bbox1 = draw.textbbox((0, 0), line1, font=font)
                        bbox2 = draw.textbbox((0, 0), line2, font=font)

                        width1 = bbox1[2] - bbox1[0]
                        width2 = bbox2[2] - bbox2[0]

                        if width1 <= max_text_width and width2 <= max_text_width:
                            line_height = bbox1[3] - bbox1[1]

                            x1 = (img_width - width1) / 2
                            x2 = (img_width - width2) / 2

                            if position == 'top':
                                y1 = 12
                                y2 = 12 + line_height + 5
                            else:
                                y2 = img_height - line_height - 15
                                y1 = y2 - line_height - 5

                            draw.text((x1, y1), line1, font=font, fill='white',
                                     stroke_width=3, stroke_fill='black')
                            draw.text((x2, y2), line2, font=font, fill='white',
                                     stroke_width=3, stroke_fill='black')
                            print(f"    [MEME] Drew {position} text (2 lines) with font size {font_size}")
                            return

            # Fallback: just draw with smallest font if nothing else worked
            print(f"    [MEME] Warning: Text may be too long, using smallest font: '{text}'")

        # Draw the text overlays
        if text_top:
            draw_meme_text(text_top, 'top')
        if text_bottom:
            draw_meme_text(text_bottom, 'bottom')

        # Convert back to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True)
        result_bytes = buffer.getvalue()
        result_base64 = base64.b64encode(result_bytes).decode('utf-8')

        result_url = f"data:image/png;base64,{result_base64}"

        print(f"[API] Text overlay added successfully")

        return jsonify({
            'success': True,
            'url': result_url,
            'text_top': text_top,
            'text_bottom': text_bottom
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-meme-text-boxes', methods=['POST'])
def add_meme_text_boxes():
    """Add multiple text boxes to meme image with custom positions, colors, and sizes"""
    try:
        data = request.json
        image_url = data.get('image_url', '')  # Base64 data URL
        text_boxes = data.get('text_boxes', [])  # Array of text box objects
        preview_width = data.get('preview_width', 480)  # Width of preview container in browser

        print(f"\n[API] Adding {len(text_boxes)} text boxes to meme...")
        print(f"    Preview width from browser: {preview_width}px")

        if not image_url:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        if not text_boxes:
            return jsonify({'success': False, 'error': 'No text boxes provided'}), 400

        import base64
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO

        # Extract base64 data from data URL
        if ',' in image_url:
            image_data = image_url.split(',')[1]
        else:
            image_data = image_url

        # Decode and open image
        image_bytes = base64.b64decode(image_data)
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert to RGB if necessary (for PNG with transparency)
        if pil_image.mode in ('RGBA', 'P'):
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            if pil_image.mode == 'RGBA':
                background.paste(pil_image, mask=pil_image.split()[-1])
            else:
                background.paste(pil_image)
            pil_image = background

        draw = ImageDraw.Draw(pil_image)
        img_width, img_height = pil_image.size

        # Calculate scale factor: how much bigger is the actual image vs the preview
        # This helps match the font size from CSS preview to PIL rendering
        scale_factor = img_width / preview_width if preview_width > 0 else 1.0
        print(f"    Image size: {img_width}x{img_height}, scale factor: {scale_factor:.2f}")

        # Process each text box
        for i, box in enumerate(text_boxes):
            text = box.get('text', '').upper()
            if not text:
                continue

            # Get position as percentage (0-100)
            x_percent = box.get('x', 50)
            y_percent = box.get('y', 50)

            # Convert percentage to pixels
            x_pos = int((x_percent / 100) * img_width)
            y_pos = int((y_percent / 100) * img_height)

            # Get styling options
            css_font_size = box.get('fontSize', 32)

            # Preview is now fixed at 480px (same as actual image size)
            # So we use the CSS font size directly - no scaling needed
            font_size = css_font_size

            # Ensure reasonable bounds
            font_size = max(16, min(font_size, 200))

            text_color = box.get('textColor', '#FFFFFF')
            font_family = box.get('fontFamily', 'Impact')
            has_shadow = box.get('textShadow', True)

            print(f"    Text box {i+1}: font_size={font_size}px, color={text_color}")

            # Try to load the font
            try:
                if font_family.lower() == 'impact':
                    font = ImageFont.truetype("impact.ttf", font_size)
                elif font_family.lower() == 'arial black':
                    font = ImageFont.truetype("arialbd.ttf", font_size)
                elif font_family.lower() == 'comic sans ms':
                    font = ImageFont.truetype("comic.ttf", font_size)
                else:
                    font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()

            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Center text on the position
            final_x = x_pos - (text_width / 2)
            final_y = y_pos - (text_height / 2)

            # Scale stroke width too
            stroke_width = max(2, int(3 * scale_factor))

            # Draw text with or without shadow/stroke
            if has_shadow:
                # Draw with black stroke for visibility
                draw.text((final_x, final_y), text, font=font, fill=text_color,
                         stroke_width=stroke_width, stroke_fill='black')
            else:
                draw.text((final_x, final_y), text, font=font, fill=text_color)

            print(f"    [MEME] Drew text box {i+1}: '{text}' at ({x_pos}, {y_pos}) with font size {font_size}")

        # Convert back to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True)
        result_bytes = buffer.getvalue()
        result_base64 = base64.b64encode(result_bytes).decode('utf-8')

        result_url = f"data:image/png;base64,{result_base64}"

        print(f"[API] Successfully added {len(text_boxes)} text boxes to meme")

        return jsonify({
            'success': True,
            'url': result_url,
            'text_boxes_count': len(text_boxes)
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check-brand-guidelines', methods=['POST'])
def check_brand_guidelines():
    """Check content against brand guidelines"""
    try:
        data = request.json
        month = data.get('month')
        news_content = data.get('news_content', '')
        tip_content = data.get('tip_content', '')
        trend_content = data.get('trend_content', '')
        ai_model = data.get('ai_model', 'chatgpt')

        print(f"\n[API] Checking brand guidelines for {month} newsletter...")

        # Load brand guidelines
        from config.brand_guidelines import BRAND_GUIDELINES, BRAND_VOICE, NEWSLETTER_GUIDELINES

        # Select the AI client
        if ai_model == 'claude' and claude_client:
            ai_client = claude_client
            model_name = "Claude"
        else:
            ai_client = openai_client
            model_name = "ChatGPT"

        print(f"  - Using {model_name} for brand check")

        # Combine all content
        full_content = f"""
        NEWS SECTION:
        {news_content}

        TIP SECTION:
        {tip_content}

        TREND SECTION:
        {trend_content}
        """

        # Build comprehensive brand guidelines prompt
        brand_check_prompt = f"""
        You are a brand consistency checker for a wedding venue newsletter using BriteCo's Editorial Style Guide.

        BRAND GUIDELINES TO CHECK:

        1. TONE & VOICE:
        - {BRAND_VOICE['tone']}
        - {BRAND_VOICE['style']}
        - Avoid: {', '.join(BRAND_VOICE['avoid'])}

        2. WEDDING LANGUAGE (MUST BE INCLUSIVE):
        - Use gender-neutral language: they/them/theirs
        - Use "wedding party" NOT "bridal party"
        - Use "groom crew" NOT "groomsmen"
        - Use "partner" or "soon-to-be spouse" NOT "bride and groom"

        3. PUNCTUATION:
        - Use serial comma in lists
        - Use em dash (—) with spaces around it
        - Put punctuation inside quotation marks
        - Use hyphen between two words modifying a noun
        - Always hyphenate "lab-grown"

        4. NUMBERS:
        - Use % symbol (not "percent")
        - Use numbers for ages (58-years-old, not fifty-eight)
        - Spell out "zero" (not "0")

        5. ABBREVIATIONS:
        - No periods in country codes (US, UK not U.S., U.K.)
        - Washington, DC (not D.C.)

        Review the following newsletter content and identify SPECIFIC phrases that need to be changed.

        Return a JSON object with an array of suggested changes:
        {{
            "suggestions": [
                {{
                    "section": "news" | "tip" | "trend",
                    "issue": "Brief description of the issue (e.g., 'Non-inclusive language', 'Missing serial comma')",
                    "original": "exact phrase from content that needs changing",
                    "suggested": "what it should be changed to",
                    "reason": "why this change is needed per brand guidelines"
                }}
            ]
        }}

        Only include items that actually need to be changed. If the content is perfect, return an empty suggestions array.

        CONTENT TO REVIEW:
        """ + full_content

        # Get brand check from AI
        brand_check = ai_client.generate_content(
            prompt=brand_check_prompt,
            max_tokens=1000  # Increased to allow for detailed suggestions
        )

        # Parse the response
        import json
        try:
            # Try to extract JSON from response (OpenAI uses 'content', Claude uses 'raw')
            check_text = brand_check.get('content') or brand_check.get('raw', '{}')
            # Remove markdown code blocks if present
            check_text = check_text.replace('```json\n', '').replace('\n```', '').replace('```', '')
            check_results = json.loads(check_text)
        except Exception as e:
            print(f"[API WARNING] Failed to parse brand check JSON: {e}")
            print(f"[API WARNING] Raw response: {str(brand_check)[:200]}")
            # Fallback if parsing fails
            check_results = {
                "suggestions": []
            }

        num_suggestions = len(check_results.get('suggestions', []))
        print(f"[API] Brand check complete - {num_suggestions} suggestions found")

        return jsonify({
            'success': True,
            'check_results': check_results,
            'checked_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-test-email', methods=['POST'])
def send_test_email():
    """Send test email using SMTP"""
    try:
        data = request.json
        email = data.get('email')
        html_content = data.get('html')

        if not email or not html_content:
            return jsonify({'success': False, 'error': 'Missing email or HTML content'}), 400

        print(f"\n[API] Sending test email to {email}...")

        # Try to send via SMTP if configured
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Get SMTP configuration from environment (optional)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')

        if smtp_user and smtp_password:
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = 'Test Newsletter - Venue Voice'
                msg['From'] = smtp_user
                msg['To'] = email

                # Attach HTML content
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)

                print(f"[API] Test email sent successfully to {email}")

                return jsonify({
                    'success': True,
                    'message': f'Test email sent to {email}'
                })

            except Exception as smtp_error:
                print(f"[API WARNING] SMTP sending failed: {smtp_error}")
                # Fall through to simulation
        else:
            print(f"[API WARNING] SMTP not configured (set SMTP_USER and SMTP_PASSWORD in .env)")

        # Simulate sending if SMTP not configured
        print(f"[API] Test email simulated (SMTP not configured)")

        return jsonify({
            'success': True,
            'message': f'Test email prepared for {email}',
            'note': 'Configure SMTP_USER and SMTP_PASSWORD in .env for real email sending'
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/push-to-ontraport', methods=['POST'])
def push_to_ontraport():
    """Push newsletter campaign to Ontraport"""
    try:
        data = request.json
        subject = data.get('subject')
        month = data.get('month', 'Newsletter')
        html_content = data.get('html')

        if not subject or not html_content:
            return jsonify({'success': False, 'error': 'Missing subject or HTML content'}), 400

        print(f"\n[ONTRAPORT] Pushing newsletter to Ontraport...")
        print(f"  - Subject: {subject}")
        print(f"  - Month: {month}")

        # Get Ontraport credentials from environment
        ontraport_app_id = os.getenv('ONTRAPORT_APP_ID', '')
        ontraport_api_key = os.getenv('ONTRAPORT_API_KEY', '')

        if ontraport_app_id and ontraport_api_key:
            try:
                # Ontraport API endpoint for creating messages
                ontraport_url = 'https://api.ontraport.com/1/message'

                # Prepare headers
                headers = {
                    'Api-Appid': ontraport_app_id,
                    'Api-Key': ontraport_api_key,
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                # Generate plain text version from HTML
                plain_text = html_to_plain_text(html_content)
                print(f"[ONTRAPORT] Generated plain text version ({len(plain_text)} chars)")

                # Prepare message data (based on user's curl example)
                payload = {
                    'objectID': '7',
                    'name': f'Venue Newsletter {month.title()}',
                    'subject': subject,
                    'type': 'e-mail',
                    'transactional_email': '0',
                    'object_type_id': '10012',
                    'from': 'custom',
                    'send_out_name': 'BriteCo Event Insurance',
                    'reply_to_email': 'eventinsurance@brite.co',
                    'send_from': 'eventinsurance@brite.co',
                    'send_to': 'email',
                    'message_body': html_content,
                    'text_body': plain_text
                }

                print(f"[ONTRAPORT] Sending request to {ontraport_url}...")

                # Create message in Ontraport
                response = requests.post(
                    ontraport_url,
                    headers=headers,
                    data=payload,
                    timeout=30
                )

                print(f"[ONTRAPORT] Response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"[ONTRAPORT] Success! Message created in Ontraport")
                    print(f"[ONTRAPORT] Response: {result}")

                    return jsonify({
                        'success': True,
                        'message': 'Newsletter successfully pushed to Ontraport',
                        'data': result
                    })
                else:
                    error_msg = f"Ontraport API error: {response.status_code} - {response.text}"
                    print(f"[ONTRAPORT ERROR] {error_msg}")
                    return jsonify({'success': False, 'error': error_msg}), 500

            except requests.exceptions.RequestException as ontraport_error:
                print(f"[ONTRAPORT ERROR] Request failed: {ontraport_error}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'error': f'Failed to connect to Ontraport: {str(ontraport_error)}'}), 500

        else:
            print(f"[ONTRAPORT WARNING] Ontraport not configured (set ONTRAPORT_APP_ID and ONTRAPORT_API_KEY in .env)")

            # Return error - credentials are required
            return jsonify({
                'success': False,
                'error': 'Ontraport credentials not configured. Please set ONTRAPORT_APP_ID and ONTRAPORT_API_KEY in .env file.'
            }), 400

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-newsletter-archive', methods=['GET'])
def get_newsletter_archive():
    """Get last 6 months of published newsletters"""
    try:
        archive_file = os.path.join('data', 'archives', 'venue-voice-archives.json')

        if not os.path.exists(archive_file):
            return jsonify({'success': True, 'newsletters': []})

        with open(archive_file, 'r', encoding='utf-8') as f:
            all_newsletters = json.load(f)

        # Return last 6 months
        recent_newsletters = all_newsletters[:6]

        print(f"[API] Retrieved {len(recent_newsletters)} archived newsletters")

        return jsonify({
            'success': True,
            'newsletters': recent_newsletters
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-newsletter-archive', methods=['POST'])
def save_newsletter_archive():
    """Save newsletter to archive when published"""
    try:
        data = request.json

        archive_file = os.path.join('data', 'archives', 'venue-voice-archives.json')

        # Load existing archives
        if os.path.exists(archive_file):
            with open(archive_file, 'r', encoding='utf-8') as f:
                archives = json.load(f)
        else:
            archives = []

        # Create new archive entry
        new_entry = {
            'id': f"venue-{data.get('year')}-{data.get('month')}",
            'month': data.get('month'),
            'year': data.get('year'),
            'date_published': datetime.now().strftime('%Y-%m-%d'),
            'sections': data.get('sections', {}),
            'html_content': data.get('html_content', ''),
            'ontraport_campaign_id': data.get('ontraport_campaign_id')
        }

        # Add to beginning of list (most recent first)
        archives.insert(0, new_entry)

        # Keep only last 12 months
        archives = archives[:12]

        # Save back to file
        os.makedirs(os.path.dirname(archive_file), exist_ok=True)
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archives, f, indent=2)

        print(f"[API] Saved newsletter archive: {new_entry['id']}")

        return jsonify({'success': True, 'message': 'Newsletter archived'})

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# NEW 4-CARD SEARCH SYSTEM
# =============================================================================

def transform_to_shared_schema(results, source_card):
    """Transform search results to shared schema used by all 4 cards"""
    transformed = []
    for r in results:
        transformed.append({
            'title': r.get('title', ''),
            'url': r.get('url', r.get('source_url', '')),
            'publisher': r.get('publisher', ''),
            'published_at': r.get('published_date', r.get('age', '')),
            'snippet': r.get('description', ''),
            'venue_implications': r.get('venue_implications', ''),
            'category': r.get('category', 'general'),
            'source_card': source_card
        })
    return transformed


def multi_search(queries: list, max_results: int = 4, exclude_urls: list = None) -> list:
    """
    Run multiple search queries and merge/deduplicate results.

    Uses a 3-query cascade strategy:
    1. Specific query (user's intent)
    2. Broader query (core terms)
    3. Fallback query (general topic)

    Stops early if we have enough results.
    """
    exclude_urls = exclude_urls or []
    all_results = []
    seen_urls = set()

    for i, query in enumerate(queries):
        print(f"[Multi-Search] Query {i+1}/{len(queries)}: {query[:80]}...")

        try:
            results = openai_client.search_web_responses_api(
                query,
                max_results=6,  # Get extra to account for deduplication
                exclude_urls=exclude_urls + list(seen_urls)
            )

            for r in results:
                url = r.get('url', '')
                if url and url not in seen_urls:
                    all_results.append(r)
                    seen_urls.add(url)

            print(f"[Multi-Search] Query {i+1} returned {len(results)} results, total unique: {len(all_results)}")

            # Stop early if we have enough
            if len(all_results) >= max_results:
                break

        except Exception as e:
            print(f"[Multi-Search] Query {i+1} failed: {e}")
            continue

    return all_results[:max_results]


@app.route('/api/v2/search-sources', methods=['POST'])
def search_sources_v2():
    """
    Source Explorer Card - searches specific industry sites with 3-query cascade
    """
    try:
        data = request.json
        query = data.get('query', 'wedding venue trends')
        source_packs = data.get('source_packs', ['wedding'])  # wedding, hospitality, business
        time_window = data.get('time_window', '30d')
        exclude_urls = data.get('exclude_urls', [])

        print(f"\n[API v2] Source Explorer: query='{query}', packs={source_packs}")

        # Expanded source pack sites (B2B and trade publications added)
        SITE_PACKS = {
            'wedding': [
                'theknot.com', 'weddingwire.com', 'brides.com', 'marthastewartweddings.com',
                'weddingpro.com', 'catersource.com', 'specialevents.com', 'weddingbusiness.com'
            ],
            'hospitality': [
                'bizbash.com', 'specialevents.com', 'hotelnewsnow.com',
                'eventindustrynews.com', 'caterersearch.com', 'meetingsnet.com', 'skift.com'
            ],
            'business': [
                'bizjournals.com', 'restaurant.org', 'nrn.com',
                'forbes.com', 'entrepreneur.com', 'inc.com'
            ]
        }

        # Collect sites from selected packs
        sites = []
        for pack in source_packs:
            sites.extend(SITE_PACKS.get(pack, []))

        # Build site: queries with 3-query cascade
        if sites:
            # Use up to 6 sites per query for better coverage
            site_query = ' OR '.join([f'site:{s}' for s in sites[:6]])

            queries = [
                # Query 1: Site-specific with user query
                f"""Search for: ({site_query}) {query}

Find recent articles from these wedding and event industry sources.
Return results with title, url, publisher, published_date, and summary.""",

                # Query 2: Site-specific with broader topic
                f"""Search for: ({site_query}) wedding venue business news

Find recent business news about wedding venues or event spaces.
Return results with title, url, publisher, published_date, and summary.""",

                # Query 3: Fallback without site restriction
                f"""Search for wedding venue industry news from trade publications.

Find articles about: {query}
Focus on business insights, trends, and industry analysis.
Return results with title, url, publisher, published_date, and summary."""
            ]
        else:
            queries = [
                f"""Search for wedding venue industry news.
Find articles about: {query}
Return results with title, url, publisher, published_date, and summary."""
            ]

        print(f"[API v2] Source Explorer using {len(sites)} sites from packs: {source_packs}")

        # Use multi-search with cascade
        search_results = multi_search(queries, max_results=8, exclude_urls=exclude_urls)

        # Transform to shared schema
        results = transform_to_shared_schema(search_results, 'explorer')

        # Enrich with GPT-5.2 story angle analysis
        results = analyze_story_angles(results, query)

        # Query summaries for UI display
        query_summaries = [
            f"1. Site-specific: {query} from {', '.join(sites[:3])}...",
            "2. Broader: wedding venue business news from sites",
            "3. Fallback: wedding venue industry news (any source)"
        ]

        return jsonify({
            'success': True,
            'results': results,
            'queries_used': query_summaries,
            'source_packs': source_packs,
            'source': 'explorer',
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API v2 ERROR] Source Explorer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'results': []}), 500


def analyze_story_angles(results: list, user_query: str) -> list:
    """
    Use LLM to analyze articles and surface interesting story angles for newsletters.
    Model selection is driven by config/vision_models.yaml task_assignments.
    """
    if not results:
        return results

    try:
        # Get model config for research enrichment task
        model_config = get_model_for_task('research_enrichment')
        model_id = model_config.get('id', 'gpt-5.2')
        max_tokens_param = model_config.get('max_tokens_param', 'max_tokens')

        print(f"[Source Explorer] Using model: {model_id}")

        # Build context for GPT
        results_text = ""
        for i, r in enumerate(results):
            results_text += f"""
Article {i+1}:
- Title: {r.get('title', '')[:100]}
- Publisher: {r.get('publisher', '')}
- Snippet: {r.get('snippet', r.get('description', ''))[:400]}
"""

        prompt = f"""You are a newsletter editor for wedding venue owners. The user searched for: "{user_query}"

Analyze these articles and surface the most interesting story angles for a venue newsletter.

Here are the articles:
{results_text}

For EACH article, provide:
1. story_angle: A compelling newsletter story angle (1-2 sentences) - what's the interesting hook for venue owners?
2. headline: A catchy headline (5-10 words) that would grab a venue owner's attention
3. why_it_matters: One sentence on why venue owners should care about this
4. content_type: One of [trend, tip, news, insight, case_study]

Return a JSON array with exactly {len(results)} objects:
[
  {{"story_angle": "...", "headline": "...", "why_it_matters": "...", "content_type": "..."}},
  ...
]

Guidelines:
- Focus on actionable insights venue owners can use
- Look for data points, trends, or tips that can be turned into content
- Headlines should be specific and engaging (not generic)
- Story angles should suggest how to write about this for venue audiences

Return ONLY the JSON array, no other text."""

        # Build API call with correct parameter name based on model
        api_params = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        api_params[max_tokens_param] = 2000

        response = openai_client.client.chat.completions.create(**api_params)

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content).strip()

        enriched = json.loads(content)

        # Merge enriched data back into results
        for i, r in enumerate(results):
            if i < len(enriched):
                r['story_angle'] = enriched[i].get('story_angle', '')
                r['headline'] = enriched[i].get('headline', r.get('title', ''))
                r['why_it_matters'] = enriched[i].get('why_it_matters', '')
                r['content_type'] = enriched[i].get('content_type', 'insight')
                # Update venue_implications with the why_it_matters
                r['venue_implications'] = enriched[i].get('why_it_matters', r.get('venue_implications', ''))

        print(f"[Source Explorer] GPT story analysis complete - enriched {len(results)} results")
        return results

    except Exception as e:
        print(f"[Source Explorer] GPT analysis error: {e} - returning original results")
        # Add default values if GPT fails
        for r in results:
            r['story_angle'] = r.get('snippet', '')[:150]
            r['headline'] = r.get('title', 'Industry Update')
            r['why_it_matters'] = 'Review this article for potential newsletter content.'
            r['content_type'] = 'insight'
        return results


def search_all_signals(time_window: str = '30d', exclude_urls: list = None) -> list:
    """
    Search ALL 5 signals simultaneously and collect results.
    Returns deduplicated results across all signal categories.
    """
    exclude_urls = exclude_urls or []

    # Signal query definitions - US-focused queries (8 signals)
    SIGNAL_QUERIES = {
        'food_costs': 'US food prices grocery costs inflation catering restaurants America recent news',
        'labor': 'US hospitality staffing shortage wages hiring event industry America recent',
        'travel': 'US airline hotel travel prices tourism hospitality trends America recent',
        'weather': 'US weather forecast climate events outdoor venues America seasonal',
        'economic': 'US consumer spending economy inflation wedding industry America market',
        'real_estate': 'US commercial real estate property prices venue lease rates America recent',
        'energy': 'US energy electricity utility costs business commercial rates America recent',
        'vendors': 'US wedding vendor prices florist catering rental equipment DJ entertainment costs America'
    }

    all_results = []
    seen_urls = set(exclude_urls)

    print(f"[Insight Builder] Searching all 8 signals (US focus)...")

    # Search each signal
    for signal, query_terms in SIGNAL_QUERIES.items():
        try:
            prompt = f"""Search for recent US news about {signal.replace('_', ' ')}.

Find articles about the United States with data points, statistics, and business impact.
Focus on American markets and US-based sources.
Search terms: {query_terms}

Return results with title, url, publisher, published_date, and summary with key data points."""

            results = openai_client.search_web_responses_api(prompt, max_results=4, exclude_urls=list(seen_urls))

            for r in results:
                url = r.get('url', '')
                if url and url not in seen_urls:
                    r['signal_source'] = signal  # Tag which signal found this
                    all_results.append(r)
                    seen_urls.add(url)

            print(f"[Insight Builder] Signal '{signal}' returned {len(results)} results")

        except Exception as e:
            print(f"[Insight Builder] Error searching signal '{signal}': {e}")
            continue

    print(f"[Insight Builder] Total unique results: {len(all_results)}")
    return all_results


def analyze_industry_impact(results: list) -> list:
    """
    Use LLM to analyze each result for event industry impact.
    Generates newsletter-ready headlines and impact scores.
    Model selection is driven by config/vision_models.yaml task_assignments.
    """
    if not results:
        return results

    try:
        # Get model config for research enrichment task
        model_config = get_model_for_task('research_enrichment')
        model_id = model_config.get('id', 'gpt-5.2')
        max_tokens_param = model_config.get('max_tokens_param', 'max_tokens')

        print(f"[Insight Builder] Using model: {model_id}")

        # Build context for GPT
        results_text = ""
        for i, r in enumerate(results):
            results_text += f"""
Result {i+1}:
- Signal: {r.get('signal_source', 'unknown')}
- Publisher: {r.get('publisher', '')}
- Raw title: {r.get('title', '')[:100]}
- Snippet: {r.get('description', r.get('snippet', ''))[:400]}
"""

        prompt = f"""You are analyzing news articles for a wedding venue industry newsletter.

For each article, determine its impact on event venues (wedding venues, event spaces, catering businesses).

Here are the articles:
{results_text}

For EACH article, provide:
1. headline: A newsletter-ready headline (5-12 words, actionable for venue owners)
2. impact: HIGH (immediate action needed), MEDIUM (worth monitoring), or LOW (FYI only)
3. signals: Array of affected categories from [food_costs, labor, travel, weather, economic, real_estate, energy, vendors]
4. so_what: One sentence explaining what venue owners should do about this

Return a JSON array with exactly {len(results)} objects:
[
  {{"headline": "...", "impact": "HIGH|MEDIUM|LOW", "signals": ["..."], "so_what": "..."}},
  ...
]

Guidelines:
- HIGH impact: price increases >5%, labor shortages, severe weather, policy changes
- MEDIUM impact: emerging trends, gradual shifts, industry forecasts
- LOW impact: general news, minor fluctuations, informational content
- Headlines should be specific with data when available (e.g., "Grocery Prices Up 4.7% - Catering Costs to Follow")

Return ONLY the JSON array, no other text."""

        # Build API call with correct parameter name based on model
        api_params = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        api_params[max_tokens_param] = 2000

        response = openai_client.client.chat.completions.create(**api_params)

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content).strip()

        enriched = json.loads(content)

        # Merge enriched data back into results
        for i, r in enumerate(results):
            if i < len(enriched):
                r['headline'] = enriched[i].get('headline', r.get('title', ''))
                r['impact'] = enriched[i].get('impact', 'MEDIUM')
                r['signals'] = enriched[i].get('signals', [r.get('signal_source', 'economic')])
                r['so_what'] = enriched[i].get('so_what', '')
                # Keep original title as fallback
                r['title'] = r['headline']

        # Sort by impact: HIGH first, then MEDIUM, then LOW
        impact_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        results.sort(key=lambda x: impact_order.get(x.get('impact', 'LOW'), 2))

        print(f"[Insight Builder] GPT analysis complete - enriched {len(results)} results")
        return results

    except Exception as e:
        print(f"[Insight Builder] GPT analysis error: {e} - returning original results")
        # Add default values if GPT fails
        for r in results:
            r['headline'] = r.get('title', 'Industry Update')
            r['impact'] = 'MEDIUM'
            r['signals'] = [r.get('signal_source', 'economic')]
            r['so_what'] = 'Monitor this trend for potential business impact.'
        return results


@app.route('/api/v2/search-insights', methods=['POST'])
def search_insights_v2():
    """
    Insight Builder Card - searches ALL 5 signals and analyzes industry impact
    """
    try:
        data = request.json
        time_window = data.get('time_window', '30d')
        exclude_urls = data.get('exclude_urls', [])

        print(f"\n[API v2] Insight Builder: Searching ALL 5 signals")

        # Step 1: Search all 5 signals simultaneously
        raw_results = search_all_signals(time_window=time_window, exclude_urls=exclude_urls)

        # Step 2: Analyze results with GPT for industry impact
        enriched_results = analyze_industry_impact(raw_results)

        # Step 3: Transform to shared schema and limit to top 8-12 results
        results = transform_to_shared_schema(enriched_results[:12], 'insight')

        # Merge back the enriched fields (headline, impact, signals, so_what)
        for i, result in enumerate(results):
            if i < len(enriched_results):
                enriched = enriched_results[i]
                result['headline'] = enriched.get('headline', result.get('title', ''))
                result['impact'] = enriched.get('impact', 'MEDIUM')
                result['signals'] = enriched.get('signals', [])
                result['so_what'] = enriched.get('so_what', '')
                result['venue_implications'] = enriched.get('so_what', '')  # Also set as venue_implications

        signals_searched = ['food_costs', 'labor', 'travel', 'weather', 'economic', 'real_estate', 'energy', 'vendors']

        return jsonify({
            'success': True,
            'results': results,
            'signals_searched': signals_searched,
            'source': 'insight',
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API v2 ERROR] Insight Builder: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'results': []}), 500


def enrich_results_with_llm(results: list, original_query: str) -> list:
    """
    Use LLM to generate newsletter-ready content from research results.
    Produces three-section format: headline, industry_data, so_what
    Model selection is driven by config/vision_models.yaml task_assignments.
    """
    if not results:
        return results

    try:
        # Get model config for research enrichment task
        model_config = get_model_for_task('research_enrichment')
        model_id = model_config.get('id', 'gpt-5.2')
        max_tokens_param = model_config.get('max_tokens_param', 'max_tokens')

        print(f"[Enrichment] Using model: {model_id}")

        # Build a single prompt to process all results at once
        results_text = ""
        for i, r in enumerate(results):
            results_text += f"""
Result {i+1}:
- URL: {r.get('url', '')}
- Publisher: {r.get('publisher', '')}
- Raw snippet: {r.get('snippet', '')[:500]}
"""

        prompt = f"""You are analyzing research findings for a wedding venue newsletter. The user searched for: "{original_query}"

Here are research findings to transform into newsletter-ready content:
{results_text}

For EACH result, extract/generate:
1. headline: A compelling newsletter headline (5-12 words, specific and actionable)
2. industry_data: The key statistic, fact, or data point from this article (1-2 sentences). Extract actual numbers/percentages when available.
3. so_what: What should venue owners DO with this information? (1 actionable sentence)
4. impact: HIGH (immediate action needed), MEDIUM (worth monitoring), or LOW (FYI only)

Return a JSON array with exactly {len(results)} objects:
[
  {{"headline": "...", "industry_data": "...", "so_what": "...", "impact": "HIGH|MEDIUM|LOW"}},
  ...
]

Guidelines:
- Headlines should be specific with data when available (e.g., "Wedding Costs Up 8% - Couples Seeking Value Packages")
- industry_data should contain the actual facts/stats from the article, not commentary
- so_what should be a specific action: "Review your...", "Consider adding...", "Update your..."
- HIGH impact: significant price changes, labor issues, policy changes affecting venues
- MEDIUM impact: emerging trends, forecasts, industry shifts
- LOW impact: general news, minor updates

Return ONLY the JSON array, no other text."""

        # Build API call with correct parameter name based on model
        api_params = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        api_params[max_tokens_param] = 2000

        response = openai_client.client.chat.completions.create(**api_params)

        content = response.choices[0].message.content.strip()

        # Parse the JSON response
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content).strip()

        enriched = json.loads(content)

        # Merge enriched data back into results
        for i, r in enumerate(results):
            if i < len(enriched):
                r['headline'] = enriched[i].get('headline', r.get('title', ''))
                r['title'] = r['headline']  # Use headline as title too
                r['industry_data'] = enriched[i].get('industry_data', r.get('snippet', ''))
                r['so_what'] = enriched[i].get('so_what', r.get('venue_implications', ''))
                r['impact'] = enriched[i].get('impact', 'MEDIUM')
                # Keep snippet for backwards compatibility
                r['snippet'] = r['industry_data']

        # Sort by impact: HIGH first, then MEDIUM, then LOW
        impact_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        results.sort(key=lambda x: impact_order.get(x.get('impact', 'LOW'), 2))

        print(f"[LLM Enrichment] Successfully enriched {len(results)} results with GPT-5.2")
        return results

    except Exception as e:
        print(f"[LLM Enrichment] Error: {e} - returning original results")
        import traceback
        traceback.print_exc()
        return results


@app.route('/api/v2/search-perplexity', methods=['POST'])
def search_perplexity_v2():
    """
    Perplexity Research Card - uses Perplexity sonar model for research with citations
    """
    try:
        data = request.json
        query = data.get('query', 'wedding venue industry news trends')
        time_window = data.get('time_window', '30d')  # 7d, 30d, 90d
        geography = data.get('geography', '')  # optional
        exclude_urls = data.get('exclude_urls', [])

        print(f"\n[API v2] Perplexity Research: query='{query}', time_window={time_window}")

        # Check if Perplexity is available
        if not perplexity_client or not perplexity_client.is_available():
            return jsonify({
                'success': False,
                'error': 'Perplexity API not configured. Add PERPLEXITY_API_KEY to .env',
                'results': []
            }), 503

        # Search using Perplexity
        search_results = perplexity_client.search_wedding_research(
            topic=query,
            geography=geography,
            time_window=time_window
        )

        # Filter out excluded URLs
        if exclude_urls:
            search_results = [r for r in search_results if r.get('url') not in exclude_urls]

        # Take top 8 results for more options
        results = search_results[:8]

        # Enrich results with LLM-generated titles and venue guidance
        if results:
            print(f"[API v2] Enriching {len(results)} Perplexity results with LLM...")
            results = enrich_results_with_llm(results, query)

        # Build query description for UI
        time_desc = {
            '7d': 'past week',
            '30d': 'past month',
            '90d': 'past 3 months'
        }.get(time_window, 'recent')

        queries_used = [
            f"Research query: {query}",
            f"Time frame: {time_desc}",
            f"Geographic focus: {geography if geography else 'US market'}"
        ]

        return jsonify({
            'success': True,
            'results': results,
            'queries_used': queries_used,
            'query': query,
            'source': 'perplexity',
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[API v2 ERROR] Perplexity Research: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'results': []}), 500


if __name__ == '__main__':
    print("=" * 80)
    print("VENUE NEWSLETTER GENERATOR - Demo API Server")
    print("=" * 80)
    print(f"\nStarting server...")
    print(f"Demo will be available at: http://localhost:5000")
    print(f"\nFeatures:")
    print(f"  [OK] Real AI content generation (OpenAI)")
    print(f"  [OK] Real image generation (Google Gemini)")
    print(f"  [OK] Current article search")
    print(f"  [OK] Seasonal trend selection")
    print(f"  [OK] Brand guidelines checking")
    print(f"\nPress Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(debug=True, port=5000, host='0.0.0.0')
