"""Pydantic models for Amazon Ads API responses.

This module provides comprehensive type definitions for all Amazon Ads API
responses, ensuring type safety and validation throughout the SDK.

The models cover all major Amazon Ads functionality including:
- Profile and account management
- Campaign and ad group management
- Keyword and targeting management
- Product ad management
- Reporting and analytics
- Performance metrics
- Error handling and batch operations
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Base Models
class BaseAPIResponse(BaseModel):
    """Base model for all API responses with common fields.

    Provides consistent configuration for all API response models
    including extra field handling, alias population, and string
    processing to accommodate API variations.
    """

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields from API
        populate_by_name=True,  # Allow field population by alias
        str_strip_whitespace=True,  # Strip whitespace from strings
    )


class PaginatedResponse(BaseAPIResponse):
    """Base model for paginated API responses.

    Provides common pagination fields that are used across
    many Amazon Ads API endpoints.

    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of results available
    :type totalResults: Optional[int]
    """

    nextToken: Optional[str] = Field(None, description="Token for next page")
    totalResults: Optional[int] = Field(None, description="Total number of results")


# Enums
class ProfileType(str, Enum):
    """Amazon Ads profile types.

    Defines the different types of advertising profiles
    available in the Amazon Ads platform.
    """

    SELLER = "SELLER"
    VENDOR = "VENDOR"
    AGENCY = "AGENCY"


class MarketplaceId(str, Enum):
    """Amazon marketplace identifiers.

    Contains the unique identifiers for all Amazon marketplaces
    where advertising is supported.
    """

    NA = "ATVPDKIKX0DER"  # US
    CA = "A2EUQ1WTGCTBG2"  # Canada
    MX = "A1AM78C64UM0Y8"  # Mexico
    BR = "A2Q3Y263D00KWC"  # Brazil
    UK = "A1F83G8C2ARO7P"  # UK
    DE = "A1PA6795UKMFR9"  # Germany
    FR = "A13V1IB3VIYZZH"  # France
    ES = "A1RKKUPIHCS9HS"  # Spain
    IT = "APJ6JRA9NG5V4"  # Italy
    NL = "A1805IZSGTT6HS"  # Netherlands
    SE = "A2NODRKZP88ZB9"  # Sweden
    PL = "A1C3SOZRARQ6R3"  # Poland
    EG = "ARBP9OOSHTCHU"  # Egypt
    TR = "A33AVAJ2PDY3EV"  # Turkey
    SA = "A17E79C6D8DWNP"  # Saudi Arabia
    AE = "A2VIGQ35RCS4UG"  # UAE
    IN = "A21TJRUUN4KGV"  # India
    JP = "A1VC38T7YXB528"  # Japan
    AU = "A39IBJ37TRP1C6"  # Australia
    SG = "A19VAU5U5O7RUS"  # Singapore


class CampaignState(str, Enum):
    """Campaign states.

    Defines the possible states a campaign can be in
    within the Amazon Ads platform.
    """

    ENABLED = "enabled"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AdGroupState(str, Enum):
    """Ad group states.

    Defines the possible states an ad group can be in
    within a campaign.
    """

    ENABLED = "enabled"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TargetingType(str, Enum):
    """Targeting types.

    Defines the different targeting strategies available
    for Amazon Ads campaigns.
    """

    KEYWORD = "keyword"
    PRODUCT = "product"
    AUTO = "auto"
    CATEGORY = "category"
    AUDIENCE = "audience"


class MatchType(str, Enum):
    """Keyword match types.

    Defines how keywords should be matched against
    customer search queries.
    """

    EXACT = "exact"
    PHRASE = "phrase"
    BROAD = "broad"


class BidOptimization(str, Enum):
    """Bid optimization strategies.

    Defines the different bid optimization approaches
    available for Amazon Ads campaigns.
    """

    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    REACH = "reach"


class ReportStatus(str, Enum):
    """Report generation status.

    Defines the possible states of a report generation
    request in the Amazon Ads platform.
    """

    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


# Profile Models
class Profile(BaseAPIResponse):
    """Amazon Ads profile/account model.

    Represents an advertising profile with marketplace,
    currency, and account information.

    :param profileId: Unique identifier for the profile
    :type profileId: str
    :param countryCode: ISO country code for the profile
    :type countryCode: str
    :param currencyCode: ISO currency code for the profile
    :type currencyCode: str
    :param timezone: Timezone for the profile
    :type timezone: str
    :param marketplaceStringId: Marketplace identifier
    :type marketplaceStringId: MarketplaceId
    :param profileType: Type of advertising profile
    :type profileType: ProfileType
    :param accountName: Optional account name
    :type accountName: Optional[str]
    :param accountId: Optional account identifier
    :type accountId: Optional[str]
    :param accountSubType: Optional account sub-type
    :type accountSubType: Optional[str]
    :param accountValidPaymentMethod: Whether account has valid payment method
    :type accountValidPaymentMethod: bool
    """

    profileId: str = Field(..., description="Unique profile identifier")
    countryCode: str = Field(..., description="Country code")
    currencyCode: str = Field(..., description="Currency code")
    timezone: str = Field(..., description="Profile timezone")
    marketplaceStringId: MarketplaceId = Field(..., description="Marketplace ID")
    profileType: ProfileType = Field(..., description="Profile type")
    accountName: Optional[str] = Field(None, description="Account name")
    accountId: Optional[str] = Field(None, description="Account ID")
    accountSubType: Optional[str] = Field(None, description="Account sub-type")
    accountValidPaymentMethod: bool = Field(True, description="Valid payment method")


class ProfileListResponse(PaginatedResponse):
    """Response for profile list operations.

    Contains a list of advertising profiles with pagination support.

    :param profiles: List of advertising profiles
    :type profiles: List[Profile]
    """

    profiles: List[Profile] = Field(default_factory=list)


# Campaign Models
class Campaign(BaseAPIResponse):
    """Campaign model.

    Represents an advertising campaign with targeting,
    budget, and performance settings.

    :param campaignId: Unique identifier for the campaign
    :type campaignId: str
    :param campaignName: Human-readable name for the campaign
    :type campaignName: str
    :param campaignType: Type of advertising campaign
    :type campaignType: str
    :param state: Current state of the campaign
    :type state: CampaignState
    :param dailyBudget: Daily budget limit for the campaign
    :type dailyBudget: Decimal
    :param startDate: When the campaign starts
    :type startDate: datetime
    :param endDate: When the campaign ends (optional)
    :type endDate: Optional[datetime]
    :param targetingType: Targeting strategy for the campaign
    :type targetingType: TargetingType
    :param bidOptimization: Bid optimization strategy
    :type bidOptimization: Optional[BidOptimization]
    :param portfolioId: Associated portfolio identifier
    :type portfolioId: Optional[str]
    :param createdDate: When the campaign was created
    :type createdDate: datetime
    :param lastUpdatedDate: When the campaign was last updated
    :type lastUpdatedDate: datetime
    :param servingStatus: Current serving status
    :type servingStatus: Optional[str]
    """

    campaignId: str = Field(..., description="Campaign ID")
    campaignName: str = Field(..., description="Campaign name")
    campaignType: str = Field(..., description="Campaign type")
    state: CampaignState = Field(..., description="Campaign state")
    dailyBudget: Decimal = Field(..., description="Daily budget")
    startDate: datetime = Field(..., description="Start date")
    endDate: Optional[datetime] = Field(None, description="End date")
    targetingType: TargetingType = Field(..., description="Targeting type")
    bidOptimization: Optional[BidOptimization] = Field(
        None, description="Bid optimization"
    )
    portfolioId: Optional[str] = Field(None, description="Portfolio ID")
    createdDate: datetime = Field(..., description="Creation date")
    lastUpdatedDate: datetime = Field(..., description="Last update date")
    servingStatus: Optional[str] = Field(None, description="Serving status")


class CampaignListResponse(PaginatedResponse):
    """Response for campaign list operations.

    Contains a list of campaigns with pagination support.

    :param campaigns: List of advertising campaigns
    :type campaigns: List[Campaign]
    """

    campaigns: List[Campaign] = Field(default_factory=list)


class CampaignCreateRequest(BaseModel):
    """Request to create a campaign.

    Contains all parameters needed to create a new
    advertising campaign.

    :param name: Name for the new campaign
    :type name: str
    :param campaignType: Type of campaign to create
    :type campaignType: str
    :param targetingType: Targeting strategy for the campaign
    :type targetingType: TargetingType
    :param state: Initial state of the campaign
    :type state: CampaignState
    :param dailyBudget: Daily budget limit
    :type dailyBudget: Decimal
    :param startDate: When the campaign should start
    :type startDate: datetime
    :param endDate: When the campaign should end (optional)
    :type endDate: Optional[datetime]
    :param portfolioId: Associated portfolio identifier
    :type portfolioId: Optional[str]
    """

    name: str = Field(..., description="Campaign name")
    campaignType: str = Field(..., description="Campaign type")
    targetingType: TargetingType = Field(..., description="Targeting type")
    state: CampaignState = Field(CampaignState.ENABLED, description="Initial state")
    dailyBudget: Decimal = Field(..., description="Daily budget")
    startDate: datetime = Field(..., description="Start date")
    endDate: Optional[datetime] = Field(None, description="End date")
    portfolioId: Optional[str] = Field(None, description="Portfolio ID")


class CampaignUpdateRequest(BaseModel):
    """Request to update a campaign.

    Contains parameters that can be modified for an
    existing advertising campaign.

    :param name: New name for the campaign
    :type name: Optional[str]
    :param state: New state for the campaign
    :type state: Optional[CampaignState]
    :param dailyBudget: New daily budget limit
    :type dailyBudget: Optional[Decimal]
    :param endDate: New end date for the campaign
    :type endDate: Optional[datetime]
    :param portfolioId: New associated portfolio identifier
    :type portfolioId: Optional[str]
    """

    name: Optional[str] = Field(None, description="Campaign name")
    state: Optional[CampaignState] = Field(None, description="Campaign state")
    dailyBudget: Optional[Decimal] = Field(None, description="Daily budget")
    endDate: Optional[datetime] = Field(None, description="End date")
    portfolioId: Optional[str] = Field(None, description="Portfolio ID")


# Ad Group Models
class AdGroup(BaseAPIResponse):
    """Ad group model.

    Represents an ad group within a campaign with
    targeting and bid settings.

    :param adGroupId: Unique identifier for the ad group
    :type adGroupId: str
    :param adGroupName: Human-readable name for the ad group
    :type adGroupName: str
    :param campaignId: Parent campaign identifier
    :type campaignId: str
    :param state: Current state of the ad group
    :type state: AdGroupState
    :param defaultBid: Default bid amount for the ad group
    :type defaultBid: Decimal
    :param createdDate: When the ad group was created
    :type createdDate: datetime
    :param lastUpdatedDate: When the ad group was last updated
    :type lastUpdatedDate: datetime
    :param servingStatus: Current serving status
    :type servingStatus: Optional[str]
    """

    adGroupId: str = Field(..., description="Ad group ID")
    adGroupName: str = Field(..., description="Ad group name")
    campaignId: str = Field(..., description="Campaign ID")
    state: AdGroupState = Field(..., description="Ad group state")
    defaultBid: Decimal = Field(..., description="Default bid")
    createdDate: datetime = Field(..., description="Creation date")
    lastUpdatedDate: datetime = Field(..., description="Last update date")
    servingStatus: Optional[str] = Field(None, description="Serving status")


class AdGroupListResponse(PaginatedResponse):
    """Response for ad group list operations.

    Contains a list of ad groups with pagination support.

    :param adGroups: List of ad groups
    :type adGroups: List[AdGroup]
    """

    adGroups: List[AdGroup] = Field(default_factory=list)


# Keyword Models
class Keyword(BaseAPIResponse):
    """Keyword targeting model.

    Represents a keyword target within an ad group
    with bid and match type settings.

    :param keywordId: Unique identifier for the keyword
    :type keywordId: str
    :param keywordText: The actual keyword text
    :type keywordText: str
    :param campaignId: Parent campaign identifier
    :type campaignId: str
    :param adGroupId: Parent ad group identifier
    :type adGroupId: str
    :param state: Current state of the keyword
    :type state: str
    :param matchType: How the keyword should be matched
    :type matchType: MatchType
    :param bid: Bid amount for the keyword
    :type bid: Decimal
    :param createdDate: When the keyword was created
    :type createdDate: datetime
    :param lastUpdatedDate: When the keyword was last updated
    :type lastUpdatedDate: datetime
    :param servingStatus: Current serving status
    :type servingStatus: Optional[str]
    """

    keywordId: str = Field(..., description="Keyword ID")
    keywordText: str = Field(..., description="Keyword text")
    campaignId: str = Field(..., description="Campaign ID")
    adGroupId: str = Field(..., description="Ad group ID")
    state: str = Field(..., description="Keyword state")
    matchType: MatchType = Field(..., description="Match type")
    bid: Decimal = Field(..., description="Keyword bid")
    createdDate: datetime = Field(..., description="Creation date")
    lastUpdatedDate: datetime = Field(..., description="Last update date")
    servingStatus: Optional[str] = Field(None, description="Serving status")


class KeywordListResponse(PaginatedResponse):
    """Response for keyword list operations.

    Contains a list of keywords with pagination support.

    :param keywords: List of keyword targets
    :type keywords: List[Keyword]
    """

    keywords: List[Keyword] = Field(default_factory=list)


# Product Ad Models
class ProductAd(BaseAPIResponse):
    """Product ad model.

    Represents a product advertisement with SKU,
    ASIN, and targeting information.

    :param adId: Unique identifier for the ad
    :type adId: str
    :param campaignId: Parent campaign identifier
    :type campaignId: str
    :param adGroupId: Parent ad group identifier
    :type adGroupId: str
    :param sku: Product SKU identifier
    :type sku: str
    :param asin: Product ASIN identifier
    :type asin: str
    :param state: Current state of the ad
    :type state: str
    :param createdDate: When the ad was created
    :type createdDate: datetime
    :param lastUpdatedDate: When the ad was last updated
    :type lastUpdatedDate: datetime
    :param servingStatus: Current serving status
    :type servingStatus: Optional[str]
    """

    adId: str = Field(..., description="Ad ID")
    campaignId: str = Field(..., description="Campaign ID")
    adGroupId: str = Field(..., description="Ad group ID")
    sku: str = Field(..., description="Product SKU")
    asin: str = Field(..., description="Product ASIN")
    state: str = Field(..., description="Ad state")
    createdDate: datetime = Field(..., description="Creation date")
    lastUpdatedDate: datetime = Field(..., description="Last update date")
    servingStatus: Optional[str] = Field(None, description="Serving status")


class ProductAdListResponse(PaginatedResponse):
    """Response for product ad list operations.

    Contains a list of product ads with pagination support.

    :param productAds: List of product advertisements
    :type productAds: List[ProductAd]
    """

    productAds: List[ProductAd] = Field(default_factory=list)


# Reporting Models
class ReportRequest(BaseModel):
    """Request to generate a report.

    Contains all parameters needed to request
    a report from the Amazon Ads API.

    :param reportType: Type of report to generate
    :type reportType: str
    :param reportDate: Date for the report data
    :type reportDate: datetime
    :param metrics: Performance metrics to include
    :type metrics: List[str]
    :param dimensions: Data dimensions to include
    :type dimensions: Optional[List[str]]
    :param filters: Optional filters for the report
    :type filters: Optional[Dict[str, Any]]
    """

    reportType: str = Field(..., description="Type of report")
    reportDate: datetime = Field(..., description="Report date")
    metrics: List[str] = Field(..., description="Metrics to include")
    dimensions: Optional[List[str]] = Field(None, description="Dimensions to include")
    filters: Optional[Dict[str, Any]] = Field(None, description="Report filters")


class ReportResponse(BaseAPIResponse):
    """Response for report generation.

    Contains information about a requested report
    including status and download location.

    :param reportId: Unique identifier for the report
    :type reportId: str
    :param reportType: Type of report requested
    :type reportType: str
    :param status: Current status of report generation
    :type status: ReportStatus
    :param statusDetails: Additional status information
    :type statusDetails: Optional[str]
    :param location: URL for downloading the report
    :type location: Optional[str]
    :param createdDate: When the report was requested
    :type createdDate: datetime
    :param completedDate: When the report was completed
    :type completedDate: Optional[datetime]
    """

    reportId: str = Field(..., description="Report ID")
    reportType: str = Field(..., description="Report type")
    status: ReportStatus = Field(..., description="Report status")
    statusDetails: Optional[str] = Field(None, description="Status details")
    location: Optional[str] = Field(None, description="Report download URL")
    createdDate: datetime = Field(..., description="Creation date")
    completedDate: Optional[datetime] = Field(None, description="Completion date")


class ReportData(BaseAPIResponse):
    """Generic report data model.

    Contains the actual data from a generated report
    with metadata about the report structure.

    :param data: List of report data rows
    :type data: List[Dict[str, Any]]
    :param metadata: Additional report metadata
    :type metadata: Dict[str, Any]
    """

    data: List[Dict[str, Any]] = Field(..., description="Report data rows")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Report metadata"
    )


# Metrics Models
class CampaignMetrics(BaseAPIResponse):
    """Campaign performance metrics.

    Contains comprehensive performance data for
    an advertising campaign.

    :param campaignId: Campaign identifier
    :type campaignId: str
    :param impressions: Number of ad impressions
    :type impressions: int
    :param clicks: Number of ad clicks
    :type clicks: int
    :param cost: Total advertising cost
    :type cost: Decimal
    :param sales: Total sales attributed to the campaign
    :type sales: Decimal
    :param orders: Number of orders attributed
    :type orders: int
    :param unitsSold: Number of units sold
    :type unitsSold: int
    :param acos: Advertising Cost of Sales percentage
    :type acos: Decimal
    :param roas: Return on Advertising Spend
    :type roas: Decimal
    :param ctr: Click-through rate
    :type ctr: Decimal
    :param cvr: Conversion rate
    :type cvr: Decimal
    :param cpc: Cost per click
    :type cpc: Decimal
    """

    campaignId: str = Field(..., description="Campaign ID")
    impressions: int = Field(..., description="Number of impressions")
    clicks: int = Field(..., description="Number of clicks")
    cost: Decimal = Field(..., description="Total cost")
    sales: Decimal = Field(..., description="Total sales")
    orders: int = Field(..., description="Number of orders")
    unitsSold: int = Field(..., description="Units sold")
    acos: Decimal = Field(..., description="ACoS percentage")
    roas: Decimal = Field(..., description="ROAS")
    ctr: Decimal = Field(..., description="Click-through rate")
    cvr: Decimal = Field(..., description="Conversion rate")
    cpc: Decimal = Field(..., description="Cost per click")


class AdGroupMetrics(BaseAPIResponse):
    """Ad group performance metrics.

    Contains comprehensive performance data for
    an advertising group.

    :param adGroupId: Ad group identifier
    :type adGroupId: str
    :param impressions: Number of ad impressions
    :type impressions: int
    :param clicks: Number of ad clicks
    :type clicks: int
    :param cost: Total advertising cost
    :type cost: Decimal
    :param sales: Total sales attributed to the ad group
    :type sales: Decimal
    :param orders: Number of orders attributed
    :type orders: int
    :param unitsSold: Number of units sold
    :type unitsSold: int
    :param acos: Advertising Cost of Sales percentage
    :type acos: Decimal
    :param roas: Return on Advertising Spend
    :type roas: Decimal
    :param ctr: Click-through rate
    :type ctr: Decimal
    :param cvr: Conversion rate
    :type cvr: Decimal
    :param cpc: Cost per click
    :type cpc: Decimal
    """

    adGroupId: str = Field(..., description="Ad group ID")
    impressions: int = Field(..., description="Number of impressions")
    clicks: int = Field(..., description="Number of clicks")
    cost: Decimal = Field(..., description="Total cost")
    sales: Decimal = Field(..., description="Total sales")
    orders: int = Field(..., description="Number of orders")
    unitsSold: int = Field(..., description="Units sold")
    acos: Decimal = Field(..., description="ACoS percentage")
    roas: Decimal = Field(..., description="ROAS")
    ctr: Decimal = Field(..., description="Click-through rate")
    cvr: Decimal = Field(..., description="Conversion rate")
    cpc: Decimal = Field(..., description="Cost per click")


# Budget Models
class BudgetRecommendation(BaseAPIResponse):
    """Budget recommendation model.

    Contains budget optimization recommendations
    for advertising campaigns.

    :param campaignId: Campaign identifier
    :type campaignId: str
    :param recommendedDailyBudget: Recommended daily budget amount
    :type recommendedDailyBudget: Decimal
    :param currentDailyBudget: Current daily budget setting
    :type currentDailyBudget: Decimal
    :param estimatedMissedImpressions: Estimated missed impressions
    :type estimatedMissedImpressions: int
    :param estimatedMissedClicks: Estimated missed clicks
    :type estimatedMissedClicks: int
    :param estimatedMissedSales: Estimated missed sales
    :type estimatedMissedSales: Decimal
    """

    campaignId: str = Field(..., description="Campaign ID")
    recommendedDailyBudget: Decimal = Field(..., description="Recommended daily budget")
    currentDailyBudget: Decimal = Field(..., description="Current daily budget")
    estimatedMissedImpressions: int = Field(
        ..., description="Estimated missed impressions"
    )
    estimatedMissedClicks: int = Field(..., description="Estimated missed clicks")
    estimatedMissedSales: Decimal = Field(..., description="Estimated missed sales")


# Error Response Models
class APIError(BaseAPIResponse):
    """API error response model.

    Contains detailed error information from
    Amazon Ads API calls.

    :param code: Error code identifier
    :type code: str
    :param message: Human-readable error message
    :type message: str
    :param details: Additional error details
    :type details: Optional[Dict[str, Any]]
    """

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class APIErrorResponse(BaseAPIResponse):
    """API error response wrapper.

    Contains multiple errors and request tracking
    information for failed API calls.

    :param errors: List of error details
    :type errors: List[APIError]
    :param requestId: Request identifier for tracking
    :type requestId: Optional[str]
    """

    errors: List[APIError] = Field(..., description="List of errors")
    requestId: Optional[str] = Field(None, description="Request ID for tracking")


# Batch Operation Models
class BatchOperationRequest(BaseModel):
    """Request for batch operations.

    Contains multiple operations to be executed
    in a single API call.

    :param operations: List of operations to execute
    :type operations: List[Dict[str, Any]]
    """

    operations: List[Dict[str, Any]] = Field(..., description="Batch operations")


class BatchOperationResponse(BaseAPIResponse):
    """Response for batch operations.

    Contains results from executing multiple
    operations in a single request.

    :param successCount: Number of successful operations
    :type successCount: int
    :param failureCount: Number of failed operations
    :type failureCount: int
    :param results: Detailed results for each operation
    :type results: List[Dict[str, Any]]
    """

    successCount: int = Field(..., description="Number of successful operations")
    failureCount: int = Field(..., description="Number of failed operations")
    results: List[Dict[str, Any]] = Field(..., description="Operation results")


# Generic Response Wrapper
class APIResponse(BaseAPIResponse):
    """Generic API response wrapper with metadata.

    Provides a standardized response structure with
    success indicators and metadata for all API calls.

    :param success: Whether the request was successful
    :type success: bool
    :param data: Response data payload
    :type data: Optional[Any]
    :param error: Error information if request failed
    :type error: Optional[APIError]
    :param metadata: Additional response metadata
    :type metadata: Dict[str, Any]
    :param requestId: Request identifier for tracking
    :type requestId: Optional[str]
    :param timestamp: When the response was generated
    :type timestamp: datetime
    """

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[APIError] = Field(None, description="Error information")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )
    requestId: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


# Export all models
__all__ = [
    # Base models
    "BaseAPIResponse",
    "PaginatedResponse",
    # Enums
    "ProfileType",
    "MarketplaceId",
    "CampaignState",
    "AdGroupState",
    "TargetingType",
    "MatchType",
    "BidOptimization",
    "ReportStatus",
    # Profile models
    "Profile",
    "ProfileListResponse",
    # Campaign models
    "Campaign",
    "CampaignListResponse",
    "CampaignCreateRequest",
    "CampaignUpdateRequest",
    # Ad group models
    "AdGroup",
    "AdGroupListResponse",
    # Keyword models
    "Keyword",
    "KeywordListResponse",
    # Product ad models
    "ProductAd",
    "ProductAdListResponse",
    # Reporting models
    "ReportRequest",
    "ReportResponse",
    "ReportData",
    # Metrics models
    "CampaignMetrics",
    "AdGroupMetrics",
    # Budget models
    "BudgetRecommendation",
    # Error models
    "APIError",
    "APIErrorResponse",
    # Batch models
    "BatchOperationRequest",
    "BatchOperationResponse",
    # Generic wrapper
    "APIResponse",
]
