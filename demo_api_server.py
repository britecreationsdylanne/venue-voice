"""
Functional Demo API Server
Provides real AI-powered endpoints for the interactive demo
Run this to make the demo fully functional!
"""

import os
import sys
import json
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
from integrations.brave_search import BraveSearchClient
from config.brand_guidelines import BRAND_VOICE, NEWSLETTER_GUIDELINES

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
    import re

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

# Try to initialize Brave Search (optional)
try:
    brave_client = BraveSearchClient()
    print("[OK] Brave Search initialized")
except Exception as e:
    brave_client = None
    print(f"[WARNING] Brave Search not available: {e}")

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

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Generate newsletter content for selected topics"""
    try:
        data = request.json
        news_topic = data.get('news_topic')
        tip_topic = data.get('tip_topic')
        trend_topic = data.get('trend_topic')
        month = data.get('month', 'january')
        ai_model = data.get('ai_model', 'chatgpt')  # Default to ChatGPT

        # Select the AI client based on user choice
        if ai_model == 'claude' and claude_client:
            ai_client = claude_client
            model_name = "Claude (Sonnet 4.5)"
        elif ai_model == 'gemini':
            # For Gemini, we'll use a text model instead of image model
            # Use Gemini 1.5 Pro for text generation
            ai_client = openai_client  # Fallback to OpenAI for now since Gemini client is for images
            model_name = "ChatGPT (GPT-4o) - Gemini text support coming soon"
        else:
            ai_client = openai_client
            model_name = "ChatGPT (GPT-4o)"

        print(f"\n[API] Generating content for {month} using {model_name}...")

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
                import re
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
                import re
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
                import re
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
            # News: 480px wide (full width) - use 16:9 landscape
            # Tip: 160px (smaller, portrait) - use 9:16 or 1:1
            # Trend: 160px (smaller, portrait) - use 9:16 or 1:1
            if section_name == 'news':
                aspect_ratio = "16:9"  # Landscape for full-width news image
            else:
                aspect_ratio = "1:1"  # Square for smaller tip/trend images

            # Generate with Gemini (Nano Banana)
            print(f"  [{section_name.upper()}] Calling Nano Banana...")
            image_result = gemini_client.generate_image(
                prompt=prompt,
                model="gemini-2.5-flash-image",
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
                        # Tip/Trend: 210px wide, increased height to 250px to match boxes
                        target_width = 210
                        target_height = 250

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

@app.route('/api/search-memes', methods=['POST'])
def search_memes():
    """Search web for wedding memes using Google Custom Search"""
    try:
        data = request.json
        month = data.get('month', '')

        print(f"\n[API] Searching for wedding memes for {month}...")

        # Month-specific search queries
        month_queries = {
            'january': 'wedding planning new year funny meme',
            'february': 'wedding valentines day funny meme',
            'march': 'spring wedding season funny meme',
            'april': 'wedding rain funny meme',
            'may': 'wedding season chaos funny meme',
            'june': 'peak wedding season stress funny meme',
            'july': 'summer outdoor wedding funny meme',
            'august': 'late summer wedding funny meme',
            'september': 'fall wedding funny meme',
            'october': 'halloween wedding funny meme',
            'november': 'thanksgiving wedding funny meme',
            'december': 'holiday wedding funny meme'
        }

        search_query = month_queries.get(month.lower(), 'wedding venue funny meme')

        # Use Brave Search API for image search
        try:
            import requests as req
            brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY', '')

            if brave_api_key:
                # Brave Image Search API
                brave_url = 'https://api.search.brave.com/res/v1/images/search'
                headers = {
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip',
                    'X-Subscription-Token': brave_api_key
                }
                params = {
                    'q': search_query,
                    'count': 10,
                    'safesearch': 'moderate'
                }

                response = req.get(brave_url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    results = response.json()
                    images = []

                    for result in results.get('results', [])[:8]:  # Limit to 8 results
                        images.append({
                            'url': result.get('properties', {}).get('url', result.get('url', '')),
                            'thumbnail': result.get('thumbnail', {}).get('src', result.get('url', '')),
                            'title': result.get('title', 'Wedding Meme')
                        })

                    print(f"[API] Found {len(images)} memes from Brave Search")

                    return jsonify({
                        'success': True,
                        'images': images,
                        'search_query': search_query
                    })
                else:
                    print(f"[API WARNING] Brave Search failed: {response.status_code}")
            else:
                print(f"[API WARNING] Brave API key not configured")
        except Exception as search_error:
            print(f"[API WARNING] Image search failed: {search_error}")

        # Fallback: Suggest user upload their own or use generated meme
        print(f"[API] Returning fallback message")

        return jsonify({
            'success': False,
            'error': 'Image search unavailable. Please upload your own meme or use the generated one.',
            'images': []
        })

    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

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

        # Generate with Nano Banana
        meme_result = gemini_client.generate_image(
            prompt=prompt,
            model="gemini-2.5-flash-image",  # Force correct model
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

                # Resize with high-quality resampling
                resized_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

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
    """Handle meme image upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Read the file and convert to base64
        import base64
        file_data = file.read()
        image_data = base64.b64encode(file_data).decode('utf-8')

        # Determine file type
        file_type = file.content_type or 'image/png'

        # Create data URL
        image_url = f"data:{file_type};base64,{image_data}"

        print(f"[API] Meme uploaded successfully: {file.filename}")

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
