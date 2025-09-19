"""Pydantic models for Amazon Stores and Brand Management API responses.

This module provides comprehensive type definitions for Amazon Stores, Brand Registry,
and related brand management API responses.

The models cover all major Stores and Brand functionality including:
- Store creation and management
- Store page and content management
- Brand registry and management
- Store analytics and performance metrics
- A+ Content (Enhanced Brand Content)
- Social commerce posts
- Store templates and customization
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StoreStatus(str, Enum):
    """Store status values.

    Defines the possible states an Amazon Store can be in
    during creation, review, and publication.
    """

    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    REJECTED = "REJECTED"
    SCHEDULED = "SCHEDULED"


class PageType(str, Enum):
    """Store page types.

    Defines the different types of pages that can be
    created within an Amazon Store.
    """

    HOME = "HOME"
    PRODUCT_GRID = "PRODUCT_GRID"
    PRODUCT_HIGHLIGHT = "PRODUCT_HIGHLIGHT"
    MARQUEE = "MARQUEE"
    GALLERY = "GALLERY"
    CUSTOM = "CUSTOM"


class BrandStatus(str, Enum):
    """Brand registry status.

    Defines the possible states a brand can be in
    within the Amazon Brand Registry.
    """

    REGISTERED = "REGISTERED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class ContentType(str, Enum):
    """Store content types.

    Defines the different types of content that can be
    added to store pages.
    """

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    PRODUCT = "PRODUCT"
    HERO = "HERO"
    CAROUSEL = "CAROUSEL"


# Base Store Model
class BaseStoreModel(BaseModel):
    """Base model for store entities.

    Provides common configuration for all store models including
    extra field handling, alias population, and string processing.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# Store Models
class Store(BaseStoreModel):
    """Amazon Store model.

    Represents an Amazon Store with all its configuration,
    content, and publication status.

    :param storeId: Unique identifier for the store
    :type storeId: str
    :param storeName: Human-readable name for the store
    :type storeName: str
    :param brandName: Associated brand name
    :type brandName: str
    :param marketplaceId: Marketplace where the store is available
    :type marketplaceId: str
    :param status: Current publication status of the store
    :type status: StoreStatus
    :param storeUrl: Public URL where the store can be accessed
    :type storeUrl: HttpUrl
    :param previewUrl: Preview URL for unpublished changes
    :type previewUrl: Optional[HttpUrl]
    :param lastPublishedDate: When the store was last published
    :type lastPublishedDate: Optional[datetime]
    :param createdAt: When the store was created
    :type createdAt: datetime
    :param updatedAt: When the store was last updated
    :type updatedAt: datetime
    :param pageCount: Number of pages in the store
    :type pageCount: int
    """

    storeId: str = Field(..., description="Store ID")
    storeName: str = Field(..., description="Store name")
    brandName: str = Field(..., description="Associated brand name")
    marketplaceId: str = Field(..., description="Marketplace ID")
    status: StoreStatus = Field(..., description="Store status")
    storeUrl: HttpUrl = Field(..., description="Public store URL")
    previewUrl: Optional[HttpUrl] = Field(None, description="Preview URL")
    lastPublishedDate: Optional[datetime] = Field(
        None, description="Last published date"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    pageCount: int = Field(..., description="Number of pages in store")


class StoreListResponse(BaseStoreModel):
    """Response for store list operations.

    Contains a list of Amazon Stores with pagination support.

    :param stores: List of Amazon Stores
    :type stores: List[Store]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of stores available
    :type totalResults: Optional[int]
    """

    stores: List[Store] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Store Page Models
class StorePage(BaseStoreModel):
    """Store page model.

    Represents a page within an Amazon Store with
    content, layout, and SEO settings.

    :param pageId: Unique identifier for the page
    :type pageId: str
    :param storeId: Parent store identifier
    :type storeId: str
    :param pageName: Human-readable name for the page
    :type pageName: str
    :param pageType: Type of page layout
    :type pageType: PageType
    :param pageUrl: URL path for the page within the store
    :type pageUrl: str
    :param isHomePage: Whether this is the store's home page
    :type isHomePage: bool
    :param parentPageId: Parent page identifier for nested pages
    :type parentPageId: Optional[str]
    :param seoTitle: SEO title for the page
    :type seoTitle: Optional[str]
    :param seoDescription: SEO description for the page
    :type seoDescription: Optional[str]
    :param status: Current publication status of the page
    :type status: StoreStatus
    :param createdAt: When the page was created
    :type createdAt: datetime
    :param updatedAt: When the page was last updated
    :type updatedAt: datetime
    """

    pageId: str = Field(..., description="Page ID")
    storeId: str = Field(..., description="Parent store ID")
    pageName: str = Field(..., description="Page name")
    pageType: PageType = Field(..., description="Page type")
    pageUrl: str = Field(..., description="Page URL path")
    isHomePage: bool = Field(False, description="Is this the home page")
    parentPageId: Optional[str] = Field(None, description="Parent page ID")
    seoTitle: Optional[str] = Field(None, description="SEO title")
    seoDescription: Optional[str] = Field(None, description="SEO description")
    status: StoreStatus = Field(..., description="Page status")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class StorePageListResponse(BaseStoreModel):
    """Response for store page list operations.

    Contains a list of store pages with pagination support.

    :param pages: List of store pages
    :type pages: List[StorePage]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    """

    pages: List[StorePage] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)


# Store Content Models
class StoreContent(BaseStoreModel):
    """Store content item model.

    Represents a content element within a store page
    such as images, text, or product showcases.

    :param contentId: Unique identifier for the content
    :type contentId: str
    :param pageId: Page where the content appears
    :type pageId: str
    :param contentType: Type of content element
    :type contentType: ContentType
    :param position: Position of the content on the page
    :type position: int
    :param contentData: Content-specific data and configuration
    :type contentData: Dict[str, Any]
    :param isActive: Whether the content is currently active
    :type isActive: bool
    :param createdAt: When the content was created
    :type createdAt: datetime
    :param updatedAt: When the content was last updated
    :type updatedAt: datetime
    """

    contentId: str = Field(..., description="Content ID")
    pageId: str = Field(..., description="Page ID where content appears")
    contentType: ContentType = Field(..., description="Content type")
    position: int = Field(..., description="Content position on page")
    contentData: Dict[str, Any] = Field(..., description="Content-specific data")
    isActive: bool = Field(True, description="Is content active")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class StoreContentListResponse(BaseStoreModel):
    """Response for store content list operations.

    Contains a list of store content items with pagination support.

    :param content: List of store content items
    :type content: List[StoreContent]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    """

    content: List[StoreContent] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)


# Brand Models
class Brand(BaseStoreModel):
    """Brand registry model.

    Represents a brand registered in the Amazon Brand Registry
    with marketplace coverage and verification status.

    :param brandId: Unique identifier for the brand
    :type brandId: str
    :param brandName: Human-readable name for the brand
    :type brandName: str
    :param brandRegistry: Brand registry number
    :type brandRegistry: str
    :param status: Current verification status of the brand
    :type status: BrandStatus
    :param marketplaces: List of marketplaces where brand is registered
    :type marketplaces: List[str]
    :param logoUrl: URL to the brand logo image
    :type logoUrl: Optional[HttpUrl]
    :param websiteUrl: Brand's official website URL
    :type websiteUrl: Optional[HttpUrl]
    :param description: Optional description of the brand
    :type description: Optional[str]
    :param registeredDate: When the brand was registered
    :type registeredDate: datetime
    :param lastUpdatedDate: When the brand was last updated
    :type lastUpdatedDate: datetime
    """

    brandId: str = Field(..., description="Brand ID")
    brandName: str = Field(..., description="Brand name")
    brandRegistry: str = Field(..., description="Brand registry number")
    status: BrandStatus = Field(..., description="Brand status")
    marketplaces: List[str] = Field(..., description="Registered marketplaces")
    logoUrl: Optional[HttpUrl] = Field(None, description="Brand logo URL")
    websiteUrl: Optional[HttpUrl] = Field(None, description="Brand website")
    description: Optional[str] = Field(None, description="Brand description")
    registeredDate: datetime = Field(..., description="Registration date")
    lastUpdatedDate: datetime = Field(..., description="Last update date")


class BrandListResponse(BaseStoreModel):
    """Response for brand list operations.

    Contains a list of brands with pagination support.

    :param brands: List of brands
    :type brands: List[Brand]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of brands available
    :type totalResults: Optional[int]
    """

    brands: List[Brand] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Brand Store Analytics
class StoreAnalytics(BaseStoreModel):
    """Store analytics data.

    Contains performance metrics for an Amazon Store
    including visitor behavior and conversion data.

    :param storeId: Store identifier
    :type storeId: str
    :param date: Date for the analytics data
    :type date: datetime
    :param visitors: Number of unique visitors
    :type visitors: int
    :param pageViews: Total number of page views
    :type pageViews: int
    :param avgTimeOnStore: Average time spent on store in seconds
    :type avgTimeOnStore: float
    :param bounceRate: Bounce rate percentage
    :type bounceRate: float
    :param conversionRate: Conversion rate percentage
    :type conversionRate: float
    :param salesAmount: Total sales amount
    :type salesAmount: float
    :param unitsOrdered: Number of units ordered
    :type unitsOrdered: int
    """

    storeId: str = Field(..., description="Store ID")
    date: datetime = Field(..., description="Analytics date")
    visitors: int = Field(..., description="Number of visitors")
    pageViews: int = Field(..., description="Number of page views")
    avgTimeOnStore: float = Field(..., description="Average time on store (seconds)")
    bounceRate: float = Field(..., description="Bounce rate percentage")
    conversionRate: float = Field(..., description="Conversion rate percentage")
    salesAmount: float = Field(..., description="Sales amount")
    unitsOrdered: int = Field(..., description="Units ordered")


class StorePageAnalytics(BaseStoreModel):
    """Store page-level analytics.

    Contains performance metrics for individual
    pages within an Amazon Store.

    :param pageId: Page identifier
    :type pageId: str
    :param date: Date for the analytics data
    :type date: datetime
    :param pageViews: Number of page views
    :type pageViews: int
    :param uniqueVisitors: Number of unique visitors
    :type uniqueVisitors: int
    :param avgTimeOnPage: Average time spent on page in seconds
    :type avgTimeOnPage: float
    :param exitRate: Exit rate percentage
    :type exitRate: float
    :param clickThroughRate: Click-through rate percentage
    :type clickThroughRate: float
    """

    pageId: str = Field(..., description="Page ID")
    date: datetime = Field(..., description="Analytics date")
    pageViews: int = Field(..., description="Number of page views")
    uniqueVisitors: int = Field(..., description="Unique visitors")
    avgTimeOnPage: float = Field(..., description="Average time on page (seconds)")
    exitRate: float = Field(..., description="Exit rate percentage")
    clickThroughRate: float = Field(..., description="Click-through rate")


# A+ Content Models
class APlusContent(BaseStoreModel):
    """A+ Content (Enhanced Brand Content) model.

    Represents enhanced brand content that can be
    displayed on product detail pages.

    :param contentId: A+ Content identifier
    :type contentId: str
    :param contentName: Human-readable name for the content
    :type contentName: str
    :param brandId: Associated brand identifier
    :type brandId: str
    :param asin: Associated product ASIN
    :type asin: str
    :param marketplaceId: Marketplace where content is displayed
    :type marketplaceId: str
    :param status: Current status of the content
    :type status: str
    :param modules: Content modules and layout configuration
    :type modules: List[Dict[str, Any]]
    :param lastUpdatedDate: When the content was last updated
    :type lastUpdatedDate: datetime
    """

    contentId: str = Field(..., description="A+ Content ID")
    contentName: str = Field(..., description="Content name")
    brandId: str = Field(..., description="Brand ID")
    asin: str = Field(..., description="Associated ASIN")
    marketplaceId: str = Field(..., description="Marketplace ID")
    status: str = Field(..., description="Content status")
    modules: List[Dict[str, Any]] = Field(..., description="Content modules")
    lastUpdatedDate: datetime = Field(..., description="Last update date")


class APlusContentListResponse(BaseStoreModel):
    """Response for A+ Content list operations.

    Contains a list of A+ Content items with pagination support.

    :param content: List of A+ Content items
    :type content: List[APlusContent]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    """

    content: List[APlusContent] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)


# Brand Metrics
class BrandMetrics(BaseStoreModel):
    """Brand-level performance metrics.

    Contains comprehensive performance data for
    a brand across all its products and campaigns.

    :param brandId: Brand identifier
    :type brandId: str
    :param date: Date for the metrics data
    :type date: datetime
    :param brandSearchVolume: Number of brand-related searches
    :type brandSearchVolume: int
    :param brandImpressions: Number of brand impressions
    :type brandImpressions: int
    :param considerationRate: Brand consideration rate percentage
    :type considerationRate: float
    :param purchaseRate: Brand purchase rate percentage
    :type purchaseRate: float
    :param repeatPurchaseRate: Repeat purchase rate percentage
    :type repeatPurchaseRate: float
    :param averageOrderValue: Average order value
    :type averageOrderValue: float
    :param newToBrandCustomers: Number of new-to-brand customers
    :type newToBrandCustomers: int
    """

    brandId: str = Field(..., description="Brand ID")
    date: datetime = Field(..., description="Metrics date")
    brandSearchVolume: int = Field(..., description="Brand search volume")
    brandImpressions: int = Field(..., description="Brand impressions")
    considerationRate: float = Field(..., description="Consideration rate")
    purchaseRate: float = Field(..., description="Purchase rate")
    repeatPurchaseRate: float = Field(..., description="Repeat purchase rate")
    averageOrderValue: float = Field(..., description="Average order value")
    newToBrandCustomers: int = Field(..., description="New-to-brand customers")


# Posts (Social Commerce)
class Post(BaseStoreModel):
    """Brand post model for social commerce.

    Represents a social media post that can be
    displayed in Amazon's social commerce features.

    :param postId: Post identifier
    :type postId: str
    :param brandId: Associated brand identifier
    :type brandId: str
    :param postType: Type of social media post
    :type postType: str
    :param title: Optional title for the post
    :type title: Optional[str]
    :param caption: Post caption text
    :type caption: str
    :param mediaUrls: URLs to media files (images, videos)
    :type mediaUrls: List[HttpUrl]
    :param productAsins: List of product ASINs tagged in the post
    :type productAsins: List[str]
    :param publishedDate: When the post was published
    :type publishedDate: datetime
    :param impressions: Number of post impressions
    :type impressions: int
    :param engagement: Total engagement with the post
    :type engagement: int
    """

    postId: str = Field(..., description="Post ID")
    brandId: str = Field(..., description="Brand ID")
    postType: str = Field(..., description="Post type")
    title: Optional[str] = Field(None, description="Post title")
    caption: str = Field(..., description="Post caption")
    mediaUrls: List[HttpUrl] = Field(..., description="Media URLs")
    productAsins: List[str] = Field(default_factory=list, description="Tagged products")
    publishedDate: datetime = Field(..., description="Published date")
    impressions: int = Field(0, description="Post impressions")
    engagement: int = Field(0, description="Total engagement")


class PostListResponse(BaseStoreModel):
    """Response for post list operations.

    Contains a list of brand posts with pagination support.

    :param posts: List of brand posts
    :type posts: List[Post]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    """

    posts: List[Post] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)


# Store Template Models
class StoreTemplate(BaseStoreModel):
    """Store template model.

    Represents a pre-designed store template that can be
    used as a starting point for store creation.

    :param templateId: Template identifier
    :type templateId: str
    :param templateName: Human-readable name for the template
    :type templateName: str
    :param templateType: Type of store template
    :type templateType: str
    :param category: Template category or industry
    :type category: str
    :param thumbnailUrl: URL to template thumbnail image
    :type thumbnailUrl: HttpUrl
    :param previewUrl: URL to preview the template
    :type previewUrl: HttpUrl
    :param isPremium: Whether this is a premium template
    :type isPremium: bool
    :param features: List of template features and capabilities
    :type features: List[str]
    """

    templateId: str = Field(..., description="Template ID")
    templateName: str = Field(..., description="Template name")
    templateType: str = Field(..., description="Template type")
    category: str = Field(..., description="Template category")
    thumbnailUrl: HttpUrl = Field(..., description="Template thumbnail")
    previewUrl: HttpUrl = Field(..., description="Template preview")
    isPremium: bool = Field(False, description="Is premium template")
    features: List[str] = Field(..., description="Template features")


# Export all models
__all__ = [
    # Enums
    "StoreStatus",
    "PageType",
    "BrandStatus",
    "ContentType",
    # Store models
    "Store",
    "StoreListResponse",
    # Page models
    "StorePage",
    "StorePageListResponse",
    # Content models
    "StoreContent",
    "StoreContentListResponse",
    # Brand models
    "Brand",
    "BrandListResponse",
    # Analytics models
    "StoreAnalytics",
    "StorePageAnalytics",
    # A+ Content models
    "APlusContent",
    "APlusContentListResponse",
    # Metrics models
    "BrandMetrics",
    # Post models
    "Post",
    "PostListResponse",
    # Template models
    "StoreTemplate",
]
