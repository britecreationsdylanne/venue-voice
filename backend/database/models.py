"""
Database models for Venue Newsletter Generator
Uses SQLAlchemy ORM
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()


class NewsletterStatus(str, enum.Enum):
    """Newsletter workflow status"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SectionType(str, enum.Enum):
    """Newsletter section types"""
    NEWS = "news"
    TIP = "tip"
    TREND = "trend"


class User(Base):
    """User accounts for the newsletter tool"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="editor")  # editor, reviewer, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    newsletters = relationship("Newsletter", back_populates="created_by_user")


class Newsletter(Base):
    """Main newsletter document"""
    __tablename__ = "newsletters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Enum(NewsletterStatus), default=NewsletterStatus.DRAFT, index=True)

    # User tracking
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by_user = relationship("User", back_populates="newsletters")

    # Meta information
    title = Column(String(500))  # e.g., "Venue Voice - January 2026"
    preheader_text = Column(Text)
    hero_image_url = Column(Text)

    # Content sections (stored as relationships)
    # See NewsletterSection model below

    # Final output
    final_html = Column(Text)  # Complete HTML email
    html_preview_url = Column(Text)  # Preview URL

    # Ontraport integration
    ontraport_campaign_id = Column(String(255), index=True)
    ontraport_message_id = Column(String(255))
    published_at = Column(DateTime)

    # QA tracking
    brand_check_passed = Column(Boolean, default=False)
    brand_check_notes = Column(JSONB)  # {issues: [], warnings: []}
    manual_qa_completed = Column(Boolean, default=False)
    manual_qa_completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    manual_qa_completed_at = Column(DateTime)

    # Relationships
    sections = relationship("NewsletterSection", back_populates="newsletter", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="newsletter", cascade="all, delete-orphan")


class NewsletterSection(Base):
    """Individual sections of a newsletter (News, Tip, Trend)"""
    __tablename__ = "newsletter_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"), nullable=False)
    section_type = Column(Enum(SectionType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Content fields
    title = Column(Text, nullable=False)
    subtitle = Column(Text)  # Used for Tips and Trends
    short_version = Column(Text)  # News only: "The Short Version"
    content = Column(Text, nullable=False)  # Main body
    secondary_content = Column(Text)  # News: "Why It Matters"

    # URLs and links
    source_url = Column(Text)  # Link to source article
    read_more_url = Column(Text)  # CTA link

    # Images
    image_url = Column(Text)
    image_prompt = Column(Text)  # AI prompt used to generate image
    image_uploaded_manually = Column(Boolean, default=False)

    # Topic selection metadata
    selected_topic_id = Column(UUID(as_uuid=True), ForeignKey("topic_suggestions.id"))
    selected_topic = relationship("TopicSuggestion")

    # AI generation metadata
    ai_model_used = Column(String(100))  # e.g., "gpt-4o", "claude-3-5-sonnet"
    generation_prompt = Column(Text)  # Prompt used for content generation
    generated_at = Column(DateTime)

    # Relationships
    newsletter = relationship("Newsletter", back_populates="sections")


class TopicSuggestion(Base):
    """AI-generated topic suggestions for newsletter sections"""
    __tablename__ = "topic_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    section_type = Column(Enum(SectionType), nullable=False, index=True)

    # Topic details
    title = Column(Text, nullable=False)
    description = Column(Text)
    keywords = Column(JSONB)  # Array of keywords
    source_urls = Column(JSONB)  # Array of source URLs

    # Research data
    research_summary = Column(Text)  # AI's research notes
    trending_score = Column(Integer)  # Relevance score (0-100)

    # Usage tracking
    used_in_newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"))
    times_suggested = Column(Integer, default=0)
    times_selected = Column(Integer, default=0)

    # AI metadata
    ai_model_used = Column(String(100))
    search_query = Column(Text)  # Query used to find this topic


class BrandGuideline(Base):
    """Configurable brand guidelines for automated checking"""
    __tablename__ = "brand_guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)

    # Guideline details
    category = Column(String(100), nullable=False, index=True)  # numbers, punctuation, tone, brand
    rule_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, default=0)  # Higher = more important

    # Validation logic
    pattern = Column(Text)  # Regex pattern to match violations
    forbidden_terms = Column(JSONB)  # Array of terms to avoid
    required_terms = Column(JSONB)  # Array of terms that should be present
    correction_mapping = Column(JSONB)  # {wrong_term: correct_term}

    # Examples
    correct_examples = Column(JSONB)
    incorrect_examples = Column(JSONB)

    # Created by
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class AuditLog(Base):
    """Audit trail for all newsletter actions"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Action details
    action = Column(String(100), nullable=False)  # created, edited, published, etc.
    entity_type = Column(String(50))  # newsletter, section, image
    entity_id = Column(UUID(as_uuid=True))

    # Change tracking
    changes = Column(JSONB)  # {field: {old: value, new: value}}
    metadata = Column(JSONB)  # Additional context

    # Relationships
    newsletter = relationship("Newsletter", back_populates="audit_logs")
    user = relationship("User")


class ImageGeneration(Base):
    """Track all AI-generated images"""
    __tablename__ = "image_generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Image details
    prompt = Column(Text, nullable=False)
    ai_model = Column(String(100))  # e.g., "gemini-2.5-flash-image"
    image_url = Column(Text)  # URL after upload to Ontraport/CDN
    temp_url = Column(Text)  # Temporary URL from AI service

    # Usage
    section_id = Column(UUID(as_uuid=True), ForeignKey("newsletter_sections.id"))
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Generation metadata
    generation_params = Column(JSONB)  # Model-specific parameters
    cost_estimate = Column(String(20))  # e.g., "$0.02"
    generation_time_ms = Column(Integer)

    # Quality tracking
    user_accepted = Column(Boolean)
    regeneration_count = Column(Integer, default=0)
    parent_image_id = Column(UUID(as_uuid=True), ForeignKey("image_generations.id"))


class ApiCallLog(Base):
    """Log all external API calls for cost tracking and debugging"""
    __tablename__ = "api_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # API details
    service = Column(String(50), nullable=False, index=True)  # openai, anthropic, perplexity, gemini, ontraport
    endpoint = Column(String(255))
    method = Column(String(10))  # GET, POST, etc.

    # Request/response
    request_data = Column(JSONB)
    response_data = Column(JSONB)
    status_code = Column(Integer)
    success = Column(Boolean, index=True)
    error_message = Column(Text)

    # Performance & cost
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)  # For LLM APIs
    cost_estimate = Column(String(20))

    # Context
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
