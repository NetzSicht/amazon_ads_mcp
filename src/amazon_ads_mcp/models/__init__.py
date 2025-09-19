"""Amazon Ads MCP models package.

This package contains all Pydantic models used throughout the Amazon Ads MCP
server, organized by API domain and functionality.
"""

# Import AMC models
from .amc_models import (  # Enums; Instance models; Query models; Audience models; Data upload models; Template models; Insight models; Privacy models; Workflow models
    AMCAudience,
    AMCAudienceCreateRequest,
    AMCAudienceListResponse,
    AMCAudienceStatus,
    AMCDataSource,
    AMCDataUpload,
    AMCDataUploadRequest,
    AMCExportFormat,
    AMCInsight,
    AMCInsightListResponse,
    AMCInstance,
    AMCInstanceListResponse,
    AMCInstanceType,
    AMCPrivacyConfig,
    AMCPrivacyLevel,
    AMCQuery,
    AMCQueryExecution,
    AMCQueryExecutionRequest,
    AMCQueryListResponse,
    AMCQueryStatus,
    AMCQueryTemplate,
    AMCQueryTemplateListResponse,
    AMCQueryType,
    AMCWorkflow,
    AMCWorkflowExecution,
)

# Import API response models
from .api_responses import (  # Base models; Enums; Profile models; Campaign models; Ad group models; Keyword models; Product ad models; Reporting models; Metrics models; Budget models; Error models; Batch models; Generic wrapper
    AdGroup,
    AdGroupListResponse,
    AdGroupMetrics,
    AdGroupState,
    APIError,
    APIErrorResponse,
    APIResponse,
    BaseAPIResponse,
    BatchOperationRequest,
    BatchOperationResponse,
    BidOptimization,
    BudgetRecommendation,
    Campaign,
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignMetrics,
    CampaignState,
    CampaignUpdateRequest,
    Keyword,
    KeywordListResponse,
    MarketplaceId,
    MatchType,
    PaginatedResponse,
    ProductAd,
    ProductAdListResponse,
    Profile,
    ProfileListResponse,
    ProfileType,
    ReportData,
    ReportRequest,
    ReportResponse,
    ReportStatus,
    TargetingType,
)

# Import existing models from base_models.py
from .base_models import (  # Auth models; OpenBridge models; Identity management models
    AuthCredentials,
    Identity,
    IdentityListResponse,
    OpenbridgeIdentity,
    SetActiveIdentityRequest,
    SetActiveIdentityResponse,
    Token,
)

# Import DSP models
from .dsp_models import (  # Enums; Order models; Line item models; Creative models; Audience models; Pixel models; Report models; Metrics models
    AudienceType,
    CreativeType,
    DSPAudience,
    DSPAudienceListResponse,
    DSPCreative,
    DSPCreativeListResponse,
    DSPEntityState,
    DSPLineItem,
    DSPLineItemListResponse,
    DSPLineItemMetrics,
    DSPMetrics,
    DSPOrder,
    DSPOrderListResponse,
    DSPOrderMetrics,
    DSPPixel,
    DSPReportRequest,
    DSPReportResponse,
    OrderGoalType,
)

# Import Stores and Brands models
from .stores_brands import (  # Enums; Store models; Page models; Content models; Brand models; Analytics models; A+ Content models; Metrics models; Post models; Template models
    APlusContent,
    APlusContentListResponse,
    Brand,
    BrandListResponse,
    BrandMetrics,
    BrandStatus,
    ContentType,
    PageType,
    Post,
    PostListResponse,
    Store,
    StoreAnalytics,
    StoreContent,
    StoreContentListResponse,
    StoreListResponse,
    StorePage,
    StorePageAnalytics,
    StorePageListResponse,
    StoreStatus,
    StoreTemplate,
)

# Export all models
__all__ = [
    # Auth models
    "Token",
    "Identity",
    "AuthCredentials",
    # OpenBridge models
    "OpenbridgeIdentity",
    # Identity management models
    "IdentityListResponse",
    "SetActiveIdentityRequest",
    "SetActiveIdentityResponse",
    # Base API models
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
    "DSPEntityState",
    "CreativeType",
    "AudienceType",
    "OrderGoalType",
    "StoreStatus",
    "PageType",
    "BrandStatus",
    "ContentType",
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
    "DSPMetrics",
    "DSPOrderMetrics",
    "DSPLineItemMetrics",
    "BrandMetrics",
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
    # DSP models
    "DSPOrder",
    "DSPOrderListResponse",
    "DSPLineItem",
    "DSPLineItemListResponse",
    "DSPCreative",
    "DSPCreativeListResponse",
    "DSPAudience",
    "DSPAudienceListResponse",
    "DSPPixel",
    "DSPReportRequest",
    "DSPReportResponse",
    # Store models
    "Store",
    "StoreListResponse",
    "StorePage",
    "StorePageListResponse",
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
    # Post models
    "Post",
    "PostListResponse",
    # Template models
    "StoreTemplate",
    # AMC Enums
    "AMCInstanceType",
    "AMCQueryStatus",
    "AMCQueryType",
    "AMCDataSource",
    "AMCExportFormat",
    "AMCAudienceStatus",
    "AMCPrivacyLevel",
    # AMC Instance models
    "AMCInstance",
    "AMCInstanceListResponse",
    # AMC Query models
    "AMCQuery",
    "AMCQueryExecution",
    "AMCQueryExecutionRequest",
    "AMCQueryListResponse",
    # AMC Audience models
    "AMCAudience",
    "AMCAudienceCreateRequest",
    "AMCAudienceListResponse",
    # AMC Data upload models
    "AMCDataUpload",
    "AMCDataUploadRequest",
    # AMC Template models
    "AMCQueryTemplate",
    "AMCQueryTemplateListResponse",
    # AMC Insight models
    "AMCInsight",
    "AMCInsightListResponse",
    # AMC Privacy models
    "AMCPrivacyConfig",
    # AMC Workflow models
    "AMCWorkflow",
    "AMCWorkflowExecution",
]
