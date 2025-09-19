"""Pydantic models for Amazon DSP (Demand-Side Platform) API responses.

This module provides comprehensive type definitions for Amazon DSP API responses,
including programmatic advertising, audiences, and creative management.

The models cover all major DSP functionality including:
- Order (campaign) management
- Line item management
- Creative asset management
- Audience targeting and management
- Conversion tracking with pixels
- Reporting and analytics
- Performance metrics
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DSPEntityState(str, Enum):
    """DSP entity states.

    Defines the possible states for DSP entities like
    orders, line items, creatives, and audiences.
    """

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"


class CreativeType(str, Enum):
    """Creative types.

    Defines the different types of creative assets
    that can be used in DSP campaigns.
    """

    DISPLAY = "DISPLAY"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    NATIVE = "NATIVE"
    CUSTOM = "CUSTOM"


class AudienceType(str, Enum):
    """Audience types.

    Defines the different types of audiences available
    for targeting in DSP campaigns.
    """

    REMARKETING = "REMARKETING"
    LOOKALIKE = "LOOKALIKE"
    CUSTOM = "CUSTOM"
    CONTEXTUAL = "CONTEXTUAL"
    DEMOGRAPHIC = "DEMOGRAPHIC"
    IN_MARKET = "IN_MARKET"


class OrderGoalType(str, Enum):
    """Order goal types.

    Defines the different campaign objectives available
    for DSP orders.
    """

    AWARENESS = "AWARENESS"
    CONSIDERATION = "CONSIDERATION"
    PERFORMANCE = "PERFORMANCE"
    REACH = "REACH"


# Base DSP Model
class BaseDSPModel(BaseModel):
    """Base model for DSP entities.

    Provides common configuration for all DSP models including
    extra field handling, alias population, and string processing.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# Order Models
class DSPOrder(BaseDSPModel):
    """DSP order (campaign) model.

    Represents a DSP advertising order with budget,
    targeting, and performance settings.

    :param orderId: Unique identifier for the order
    :type orderId: str
    :param orderName: Human-readable name for the order
    :type orderName: str
    :param advertiserId: Associated advertiser identifier
    :type advertiserId: str
    :param state: Current state of the order
    :type state: DSPEntityState
    :param orderGoalType: Campaign objective for the order
    :type orderGoalType: OrderGoalType
    :param budget: Total budget for the order
    :type budget: Decimal
    :param startDateTime: When the order starts
    :type startDateTime: datetime
    :param endDateTime: When the order ends (optional)
    :type endDateTime: Optional[datetime]
    :param currency: Currency code for budget amounts
    :type currency: str
    :param createdAt: When the order was created
    :type createdAt: datetime
    :param lastUpdatedAt: When the order was last updated
    :type lastUpdatedAt: datetime
    """

    orderId: str = Field(..., description="Order ID")
    orderName: str = Field(..., description="Order name")
    advertiserId: str = Field(..., description="Advertiser ID")
    state: DSPEntityState = Field(..., description="Order state")
    orderGoalType: OrderGoalType = Field(..., description="Order goal type")
    budget: Decimal = Field(..., description="Total budget")
    startDateTime: datetime = Field(..., description="Start date and time")
    endDateTime: Optional[datetime] = Field(None, description="End date and time")
    currency: str = Field(..., description="Currency code")
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedAt: datetime = Field(..., description="Last update timestamp")


class DSPOrderListResponse(BaseDSPModel):
    """Response for DSP order list operations.

    Contains a list of DSP orders with pagination support.

    :param orders: List of DSP orders
    :type orders: List[DSPOrder]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of orders available
    :type totalResults: Optional[int]
    """

    orders: List[DSPOrder] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Line Item Models
class DSPLineItem(BaseDSPModel):
    """DSP line item model.

    Represents a line item within a DSP order with
    targeting, budget, and bid settings.

    :param lineItemId: Unique identifier for the line item
    :type lineItemId: str
    :param lineItemName: Human-readable name for the line item
    :type lineItemName: str
    :param orderId: Parent order identifier
    :type orderId: str
    :param state: Current state of the line item
    :type state: DSPEntityState
    :param budget: Budget allocated to the line item
    :type budget: Decimal
    :param bidPrice: Bid price for the line item
    :type bidPrice: Decimal
    :param startDateTime: When the line item starts
    :type startDateTime: datetime
    :param endDateTime: When the line item ends (optional)
    :type endDateTime: Optional[datetime]
    :param frequencyCap: Frequency cap settings for the line item
    :type frequencyCap: Optional[Dict[str, Any]]
    :param targetingClauses: Targeting rules for the line item
    :type targetingClauses: List[Dict[str, Any]]
    :param createdAt: When the line item was created
    :type createdAt: datetime
    :param lastUpdatedAt: When the line item was last updated
    :type lastUpdatedAt: datetime
    """

    lineItemId: str = Field(..., description="Line item ID")
    lineItemName: str = Field(..., description="Line item name")
    orderId: str = Field(..., description="Parent order ID")
    state: DSPEntityState = Field(..., description="Line item state")
    budget: Decimal = Field(..., description="Line item budget")
    bidPrice: Decimal = Field(..., description="Bid price")
    startDateTime: datetime = Field(..., description="Start date and time")
    endDateTime: Optional[datetime] = Field(None, description="End date and time")
    frequencyCap: Optional[Dict[str, Any]] = Field(
        None, description="Frequency cap settings"
    )
    targetingClauses: List[Dict[str, Any]] = Field(
        default_factory=list, description="Targeting clauses"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedAt: datetime = Field(..., description="Last update timestamp")


class DSPLineItemListResponse(BaseDSPModel):
    """Response for DSP line item list operations.

    Contains a list of DSP line items with pagination support.

    :param lineItems: List of DSP line items
    :type lineItems: List[DSPLineItem]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of line items available
    :type totalResults: Optional[int]
    """

    lineItems: List[DSPLineItem] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Creative Models
class DSPCreative(BaseDSPModel):
    """DSP creative model.

    Represents a creative asset that can be used in
    DSP advertising campaigns.

    :param creativeId: Unique identifier for the creative
    :type creativeId: str
    :param creativeName: Human-readable name for the creative
    :type creativeName: str
    :param advertiserId: Associated advertiser identifier
    :type advertiserId: str
    :param creativeType: Type of creative asset
    :type creativeType: CreativeType
    :param state: Current state of the creative
    :type state: DSPEntityState
    :param dimensions: Creative dimensions (width x height)
    :type dimensions: Dict[str, int]
    :param fileSize: Size of the creative file in bytes
    :type fileSize: Optional[int]
    :param duration: Duration in seconds (for video/audio creatives)
    :type duration: Optional[int]
    :param clickThroughUrl: Click-through URL for the creative
    :type clickThroughUrl: Optional[str]
    :param createdAt: When the creative was created
    :type createdAt: datetime
    :param lastUpdatedAt: When the creative was last updated
    :type lastUpdatedAt: datetime
    """

    creativeId: str = Field(..., description="Creative ID")
    creativeName: str = Field(..., description="Creative name")
    advertiserId: str = Field(..., description="Advertiser ID")
    creativeType: CreativeType = Field(..., description="Creative type")
    state: DSPEntityState = Field(..., description="Creative state")
    dimensions: Dict[str, int] = Field(..., description="Creative dimensions")
    fileSize: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[int] = Field(
        None, description="Duration in seconds (for video/audio)"
    )
    clickThroughUrl: Optional[str] = Field(None, description="Click-through URL")
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedAt: datetime = Field(..., description="Last update timestamp")


class DSPCreativeListResponse(BaseDSPModel):
    """Response for DSP creative list operations.

    Contains a list of DSP creatives with pagination support.

    :param creatives: List of DSP creatives
    :type creatives: List[DSPCreative]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of creatives available
    :type totalResults: Optional[int]
    """

    creatives: List[DSPCreative] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Audience Models
class DSPAudience(BaseDSPModel):
    """DSP audience model.

    Represents a targetable audience for DSP campaigns
    with targeting rules and size estimates.

    :param audienceId: Unique identifier for the audience
    :type audienceId: str
    :param audienceName: Human-readable name for the audience
    :type audienceName: str
    :param advertiserId: Associated advertiser identifier
    :type advertiserId: str
    :param audienceType: Type of audience targeting
    :type audienceType: AudienceType
    :param state: Current state of the audience
    :type state: DSPEntityState
    :param audienceSize: Estimated number of users in the audience
    :type audienceSize: Optional[int]
    :param description: Optional description of the audience
    :type description: Optional[str]
    :param rules: Targeting rules that define the audience
    :type rules: List[Dict[str, Any]]
    :param createdAt: When the audience was created
    :type createdAt: datetime
    :param lastUpdatedAt: When the audience was last updated
    :type lastUpdatedAt: datetime
    """

    audienceId: str = Field(..., description="Audience ID")
    audienceName: str = Field(..., description="Audience name")
    advertiserId: str = Field(..., description="Advertiser ID")
    audienceType: AudienceType = Field(..., description="Audience type")
    state: DSPEntityState = Field(..., description="Audience state")
    audienceSize: Optional[int] = Field(None, description="Estimated audience size")
    description: Optional[str] = Field(None, description="Audience description")
    rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Audience rules"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedAt: datetime = Field(..., description="Last update timestamp")


class DSPAudienceListResponse(BaseDSPModel):
    """Response for DSP audience list operations.

    Contains a list of DSP audiences with pagination support.

    :param audiences: List of DSP audiences
    :type audiences: List[DSPAudience]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of audiences available
    :type totalResults: Optional[int]
    """

    audiences: List[DSPAudience] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Pixel Models
class DSPPixel(BaseDSPModel):
    """DSP pixel model for conversion tracking.

    Represents a tracking pixel that can be placed on
    websites to track conversions and user behavior.

    :param pixelId: Unique identifier for the pixel
    :type pixelId: str
    :param pixelName: Human-readable name for the pixel
    :type pixelName: str
    :param advertiserId: Associated advertiser identifier
    :type advertiserId: str
    :param pixelType: Type of tracking pixel
    :type pixelType: str
    :param state: Current state of the pixel
    :type state: DSPEntityState
    :param pixelCode: HTML/JavaScript code for the pixel
    :type pixelCode: str
    :param conversionEvents: Events that the pixel tracks
    :type conversionEvents: List[Dict[str, Any]]
    :param createdAt: When the pixel was created
    :type createdAt: datetime
    :param lastUpdatedAt: When the pixel was last updated
    :type lastUpdatedAt: datetime
    """

    pixelId: str = Field(..., description="Pixel ID")
    pixelName: str = Field(..., description="Pixel name")
    advertiserId: str = Field(..., description="Advertiser ID")
    pixelType: str = Field(..., description="Pixel type")
    state: DSPEntityState = Field(..., description="Pixel state")
    pixelCode: str = Field(..., description="Pixel implementation code")
    conversionEvents: List[Dict[str, Any]] = Field(
        default_factory=list, description="Conversion events"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedAt: datetime = Field(..., description="Last update timestamp")


# Report Models
class DSPReportRequest(BaseDSPModel):
    """Request to generate a DSP report.

    Contains all parameters needed to request
    a report from the Amazon DSP API.

    :param reportType: Type of DSP report to generate
    :type reportType: str
    :param startDate: Start date for the report data
    :type startDate: datetime
    :param endDate: End date for the report data
    :type endDate: datetime
    :param dimensions: Data dimensions to include in the report
    :type dimensions: List[str]
    :param metrics: Performance metrics to include in the report
    :type metrics: List[str]
    :param filters: Optional filters for the report data
    :type filters: Optional[Dict[str, Any]]
    :param granularity: Time granularity for the report (default: "DAILY")
    :type granularity: Optional[str]
    """

    reportType: str = Field(..., description="Type of DSP report")
    startDate: datetime = Field(..., description="Report start date")
    endDate: datetime = Field(..., description="Report end date")
    dimensions: List[str] = Field(..., description="Report dimensions")
    metrics: List[str] = Field(..., description="Report metrics")
    filters: Optional[Dict[str, Any]] = Field(None, description="Report filters")
    granularity: Optional[str] = Field("DAILY", description="Report granularity")


class DSPReportResponse(BaseDSPModel):
    """Response for DSP report generation.

    Contains information about a requested DSP report
    including status and download location.

    :param reportId: Unique identifier for the report
    :type reportId: str
    :param reportType: Type of report requested
    :type reportType: str
    :param status: Current status of report generation
    :type status: str
    :param downloadUrl: URL for downloading the completed report
    :type downloadUrl: Optional[str]
    :param expiresAt: When the download URL expires
    :type expiresAt: Optional[datetime]
    :param createdAt: When the report was requested
    :type createdAt: datetime
    """

    reportId: str = Field(..., description="Report ID")
    reportType: str = Field(..., description="Report type")
    status: str = Field(..., description="Report status")
    downloadUrl: Optional[str] = Field(None, description="Report download URL")
    expiresAt: Optional[datetime] = Field(None, description="URL expiration time")
    createdAt: datetime = Field(..., description="Creation timestamp")


# Metrics Models
class DSPMetrics(BaseDSPModel):
    """DSP performance metrics.

    Contains comprehensive performance data for
    DSP advertising campaigns and line items.

    :param impressions: Number of ad impressions
    :type impressions: int
    :param clicks: Number of ad clicks
    :type clicks: int
    :param conversions: Number of conversions
    :type conversions: int
    :param spend: Total advertising spend
    :type spend: Decimal
    :param ctr: Click-through rate
    :type ctr: Decimal
    :param cvr: Conversion rate
    :type cvr: Decimal
    :param cpc: Cost per click
    :type cpc: Decimal
    :param cpm: Cost per mille (thousand impressions)
    :type cpm: Decimal
    :param cpa: Cost per acquisition
    :type cpa: Decimal
    :param viewability: Viewability rate percentage
    :type viewability: Optional[Decimal]
    :param videoCompletionRate: Video completion rate percentage
    :type videoCompletionRate: Optional[Decimal]
    """

    impressions: int = Field(..., description="Number of impressions")
    clicks: int = Field(..., description="Number of clicks")
    conversions: int = Field(..., description="Number of conversions")
    spend: Decimal = Field(..., description="Total spend")
    ctr: Decimal = Field(..., description="Click-through rate")
    cvr: Decimal = Field(..., description="Conversion rate")
    cpc: Decimal = Field(..., description="Cost per click")
    cpm: Decimal = Field(..., description="Cost per mille")
    cpa: Decimal = Field(..., description="Cost per acquisition")
    viewability: Optional[Decimal] = Field(None, description="Viewability rate")
    videoCompletionRate: Optional[Decimal] = Field(
        None, description="Video completion rate"
    )


class DSPOrderMetrics(DSPMetrics):
    """DSP order-level metrics.

    Contains performance metrics for a specific
    DSP order (campaign).

    :param orderId: Order identifier
    :type orderId: str
    :param date: Date for the metrics data
    :type date: datetime
    """

    orderId: str = Field(..., description="Order ID")
    date: datetime = Field(..., description="Metrics date")


class DSPLineItemMetrics(DSPMetrics):
    """DSP line item-level metrics.

    Contains performance metrics for a specific
    DSP line item.

    :param lineItemId: Line item identifier
    :type lineItemId: str
    :param date: Date for the metrics data
    :type date: datetime
    """

    lineItemId: str = Field(..., description="Line item ID")
    date: datetime = Field(..., description="Metrics date")


# Export all models
__all__ = [
    # Enums
    "DSPEntityState",
    "CreativeType",
    "AudienceType",
    "OrderGoalType",
    # Order models
    "DSPOrder",
    "DSPOrderListResponse",
    # Line item models
    "DSPLineItem",
    "DSPLineItemListResponse",
    # Creative models
    "DSPCreative",
    "DSPCreativeListResponse",
    # Audience models
    "DSPAudience",
    "DSPAudienceListResponse",
    # Pixel models
    "DSPPixel",
    # Report models
    "DSPReportRequest",
    "DSPReportResponse",
    # Metrics models
    "DSPMetrics",
    "DSPOrderMetrics",
    "DSPLineItemMetrics",
]
