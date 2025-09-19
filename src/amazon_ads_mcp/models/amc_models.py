"""Pydantic models for Amazon Marketing Cloud (AMC) API responses.

This module provides comprehensive type definitions for Amazon Marketing Cloud
API responses, including data clean rooms, custom queries, audiences, and
privacy-safe analytics.

The models cover all major AMC functionality including:
- Instance management and configuration
- Query execution and management
- Audience creation and management
- Data upload and processing
- Query templates and insights
- Privacy and compliance settings
- Workflow automation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AMCQueryStatus(str, Enum):
    """AMC query execution status.

    Represents the various states a query can be in during
    execution in the Amazon Marketing Cloud.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class AMCQueryType(str, Enum):
    """AMC query types.

    Defines the different types of queries that can be
    executed in Amazon Marketing Cloud.
    """

    SQL = "SQL"
    INSTRUCTIONAL = "INSTRUCTIONAL"
    TEMPLATE = "TEMPLATE"
    SAVED = "SAVED"


class AMCDataSource(str, Enum):
    """AMC data sources.

    Lists all available data sources that can be queried
    in Amazon Marketing Cloud.
    """

    AMAZON_ADS = "AMAZON_ADS"
    AMAZON_DSP = "AMAZON_DSP"
    AMAZON_ATTRIBUTION = "AMAZON_ATTRIBUTION"
    RETAIL = "RETAIL"
    STREAMING_TV = "STREAMING_TV"
    CUSTOM_UPLOAD = "CUSTOM_UPLOAD"
    FIRST_PARTY = "FIRST_PARTY"


class AMCAudienceStatus(str, Enum):
    """AMC audience status.

    Represents the various states an audience can be in
    during creation and management.
    """

    ACTIVE = "ACTIVE"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"


class AMCPrivacyLevel(str, Enum):
    """Privacy threshold levels.

    Defines the different privacy protection levels available
    for AMC queries and data processing.
    """

    STANDARD = "STANDARD"
    STRICT = "STRICT"
    CUSTOM = "CUSTOM"


class AMCExportFormat(str, Enum):
    """Export format options.

    Lists all supported export formats for AMC query results
    and data downloads.
    """

    CSV = "CSV"
    PARQUET = "PARQUET"
    JSON = "JSON"
    AVRO = "AVRO"


class AMCInstanceType(str, Enum):
    """AMC instance types.

    Defines the different types of AMC instances available
    for different use cases and environments.
    """

    PRODUCTION = "PRODUCTION"
    SANDBOX = "SANDBOX"
    DEVELOPMENT = "DEVELOPMENT"


# Base AMC Model
class BaseAMCModel(BaseModel):
    """Base model for AMC entities.

    Provides common configuration for all AMC models including
    extra field handling, alias population, and string processing.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# AMC Instance Models
class AMCInstance(BaseAMCModel):
    """AMC instance model.

    Represents an Amazon Marketing Cloud instance with all
    its configuration and metadata.

    :param instanceId: Unique identifier for the AMC instance
    :type instanceId: str
    :param instanceName: Human-readable name for the instance
    :type instanceName: str
    :param instanceType: Type of instance (production, sandbox, etc.)
    :type instanceType: AMCInstanceType
    :param region: AWS region where the instance is located
    :type region: str
    :param advertiserId: Associated advertiser identifier
    :type advertiserId: str
    :param dataSources: List of available data sources for this instance
    :type dataSources: List[AMCDataSource]
    :param createdAt: When the instance was created
    :type createdAt: datetime
    :param lastAccessedAt: When the instance was last accessed
    :type lastAccessedAt: Optional[datetime]
    :param settings: Additional instance configuration settings
    :type settings: Dict[str, Any]
    """

    instanceId: str = Field(..., description="AMC instance ID")
    instanceName: str = Field(..., description="Instance name")
    instanceType: AMCInstanceType = Field(..., description="Instance type")
    region: str = Field(..., description="AWS region")
    advertiserId: str = Field(..., description="Advertiser ID")
    dataSources: List[AMCDataSource] = Field(..., description="Available data sources")
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastAccessedAt: Optional[datetime] = Field(
        None, description="Last accessed timestamp"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Instance settings"
    )


class AMCInstanceListResponse(BaseAMCModel):
    """Response for AMC instance list operations.

    Contains a list of AMC instances with pagination support.

    :param instances: List of AMC instances
    :type instances: List[AMCInstance]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of instances available
    :type totalResults: Optional[int]
    """

    instances: List[AMCInstance] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Query Models
class AMCQuery(BaseAMCModel):
    """AMC query model.

    Represents a saved query in Amazon Marketing Cloud with
    all its metadata and configuration.

    :param queryId: Unique identifier for the query
    :type queryId: str
    :param queryName: Human-readable name for the query
    :type queryName: str
    :param instanceId: AMC instance where the query is stored
    :type instanceId: str
    :param queryType: Type of query (SQL, template, etc.)
    :type queryType: AMCQueryType
    :param queryText: The actual SQL query text
    :type queryText: str
    :param parameters: Optional parameters for the query
    :type parameters: Optional[Dict[str, Any]]
    :param description: Optional description of the query
    :type description: Optional[str]
    :param tags: List of tags associated with the query
    :type tags: List[str]
    :param createdBy: User ID who created the query
    :type createdBy: str
    :param createdAt: When the query was created
    :type createdAt: datetime
    :param lastModifiedAt: When the query was last modified
    :type lastModifiedAt: datetime
    :param isPublic: Whether the query is publicly accessible
    :type isPublic: bool
    """

    queryId: str = Field(..., description="Query ID")
    queryName: str = Field(..., description="Query name")
    instanceId: str = Field(..., description="AMC instance ID")
    queryType: AMCQueryType = Field(..., description="Query type")
    queryText: str = Field(..., description="SQL query text")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    description: Optional[str] = Field(None, description="Query description")
    tags: List[str] = Field(default_factory=list, description="Query tags")
    createdBy: str = Field(..., description="Creator user ID")
    createdAt: datetime = Field(..., description="Creation timestamp")
    lastModifiedAt: datetime = Field(..., description="Last modification timestamp")
    isPublic: bool = Field(False, description="Is query public")


class AMCQueryExecution(BaseAMCModel):
    """AMC query execution model.

    Represents a single execution of an AMC query with
    performance metrics and results.

    :param executionId: Unique identifier for the execution
    :type executionId: str
    :param queryId: ID of the query that was executed
    :type queryId: str
    :param instanceId: AMC instance where execution occurred
    :type instanceId: str
    :param status: Current status of the execution
    :type status: AMCQueryStatus
    :param startTime: When execution began
    :type startTime: datetime
    :param endTime: When execution completed (if finished)
    :type endTime: Optional[datetime]
    :param durationSeconds: Total execution time in seconds
    :type durationSeconds: Optional[int]
    :param outputLocation: S3 location where results are stored
    :type outputLocation: Optional[str]
    :param outputFormat: Format of the output data
    :type outputFormat: AMCExportFormat
    :param rowCount: Number of rows in the result set
    :type rowCount: Optional[int]
    :param errorMessage: Error details if execution failed
    :type errorMessage: Optional[str]
    :param queryPlan: Query execution plan details
    :type queryPlan: Optional[Dict[str, Any]]
    :param statistics: Performance statistics for the execution
    :type statistics: Optional[Dict[str, Any]]
    """

    executionId: str = Field(..., description="Execution ID")
    queryId: str = Field(..., description="Query ID")
    instanceId: str = Field(..., description="AMC instance ID")
    status: AMCQueryStatus = Field(..., description="Execution status")
    startTime: datetime = Field(..., description="Execution start time")
    endTime: Optional[datetime] = Field(None, description="Execution end time")
    durationSeconds: Optional[int] = Field(None, description="Execution duration")
    outputLocation: Optional[str] = Field(None, description="S3 output location")
    outputFormat: AMCExportFormat = Field(..., description="Output format")
    rowCount: Optional[int] = Field(None, description="Result row count")
    errorMessage: Optional[str] = Field(None, description="Error message if failed")
    queryPlan: Optional[Dict[str, Any]] = Field(
        None, description="Query execution plan"
    )
    statistics: Optional[Dict[str, Any]] = Field(
        None, description="Execution statistics"
    )


class AMCQueryExecutionRequest(BaseAMCModel):
    """Request to execute an AMC query.

    Contains all parameters needed to execute a query in
    Amazon Marketing Cloud.

    :param queryId: ID of a saved query to execute
    :type queryId: Optional[str]
    :param queryText: Ad-hoc SQL query text to execute
    :type queryText: Optional[str]
    :param parameters: Parameters to substitute in the query
    :type parameters: Optional[Dict[str, Any]]
    :param outputFormat: Desired format for query results
    :type outputFormat: AMCExportFormat
    :param outputLocation: Custom S3 location for results
    :type outputLocation: Optional[str]
    :param timeRange: Time range constraints for the query
    :type timeRange: Optional[Dict[str, str]]
    :param privacySettings: Privacy and compliance settings
    :type privacySettings: Optional[Dict[str, Any]]
    """

    queryId: Optional[str] = Field(None, description="Saved query ID")
    queryText: Optional[str] = Field(None, description="Ad-hoc query text")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    outputFormat: AMCExportFormat = Field(
        AMCExportFormat.CSV, description="Output format"
    )
    outputLocation: Optional[str] = Field(None, description="Custom S3 output location")
    timeRange: Optional[Dict[str, str]] = Field(
        None, description="Time range for query"
    )
    privacySettings: Optional[Dict[str, Any]] = Field(
        None, description="Privacy settings"
    )


class AMCQueryListResponse(BaseAMCModel):
    """Response for AMC query list operations.

    Contains a list of AMC queries with pagination support.

    :param queries: List of AMC queries
    :type queries: List[AMCQuery]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of queries available
    :type totalResults: Optional[int]
    """

    queries: List[AMCQuery] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Audience Models
class AMCAudience(BaseAMCModel):
    """AMC audience model.

    Represents a targetable audience created from AMC query results
    with activation and refresh capabilities.

    :param audienceId: Unique identifier for the audience
    :type audienceId: str
    :param audienceName: Human-readable name for the audience
    :type audienceName: str
    :param instanceId: AMC instance where audience is stored
    :type instanceId: str
    :param queryId: ID of the query used to create the audience
    :type queryId: str
    :param status: Current status of the audience
    :type status: AMCAudienceStatus
    :param audienceSize: Estimated number of users in the audience
    :type audienceSize: Optional[int]
    :param matchRate: Percentage of users that match the criteria
    :type matchRate: Optional[float]
    :param description: Optional description of the audience
    :type description: Optional[str]
    :param refreshSchedule: Cron expression for automatic refresh
    :type refreshSchedule: Optional[str]
    :param lastRefreshedAt: When the audience was last refreshed
    :type lastRefreshedAt: Optional[datetime]
    :param expiresAt: When the audience expires
    :type expiresAt: Optional[datetime]
    :param destinations: List of activation destinations
    :type destinations: List[str]
    :param createdAt: When the audience was created
    :type createdAt: datetime
    :param updatedAt: When the audience was last updated
    :type updatedAt: datetime
    """

    audienceId: str = Field(..., description="Audience ID")
    audienceName: str = Field(..., description="Audience name")
    instanceId: str = Field(..., description="AMC instance ID")
    queryId: str = Field(..., description="Source query ID")
    status: AMCAudienceStatus = Field(..., description="Audience status")
    audienceSize: Optional[int] = Field(None, description="Estimated audience size")
    matchRate: Optional[float] = Field(None, description="Match rate percentage")
    description: Optional[str] = Field(None, description="Audience description")
    refreshSchedule: Optional[str] = Field(None, description="Refresh schedule (cron)")
    lastRefreshedAt: Optional[datetime] = Field(
        None, description="Last refresh timestamp"
    )
    expiresAt: Optional[datetime] = Field(None, description="Expiration timestamp")
    destinations: List[str] = Field(
        default_factory=list, description="Activation destinations"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class AMCAudienceCreateRequest(BaseAMCModel):
    """Request to create an AMC audience.

    Contains all parameters needed to create a new audience
    from AMC query results.

    :param audienceName: Name for the new audience
    :type audienceName: str
    :param queryId: ID of the query to use for audience creation
    :type queryId: str
    :param description: Optional description of the audience
    :type description: Optional[str]
    :param refreshSchedule: Cron expression for automatic refresh
    :type refreshSchedule: Optional[str]
    :param ttlDays: Number of days the audience should live
    :type ttlDays: Optional[int]
    :param destinations: List of activation destinations
    :type destinations: List[str]
    """

    audienceName: str = Field(..., description="Audience name")
    queryId: str = Field(..., description="Source query ID")
    description: Optional[str] = Field(None, description="Audience description")
    refreshSchedule: Optional[str] = Field(None, description="Refresh schedule (cron)")
    ttlDays: Optional[int] = Field(30, description="Time to live in days")
    destinations: List[str] = Field(
        default_factory=list, description="Activation destinations"
    )


class AMCAudienceListResponse(BaseAMCModel):
    """Response for AMC audience list operations.

    Contains a list of AMC audiences with pagination support.

    :param audiences: List of AMC audiences
    :type audiences: List[AMCAudience]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of audiences available
    :type totalResults: Optional[int]
    """

    audiences: List[AMCAudience] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Data Upload Models
class AMCDataUpload(BaseAMCModel):
    """AMC data upload model.

    Represents a data upload to Amazon Marketing Cloud with
    processing status and metadata.

    :param uploadId: Unique identifier for the upload
    :type uploadId: str
    :param instanceId: AMC instance where data was uploaded
    :type instanceId: str
    :param datasetName: Name of the uploaded dataset
    :type datasetName: str
    :param uploadStatus: Current status of the upload
    :type uploadStatus: str
    :param fileSize: Size of the uploaded file in bytes
    :type fileSize: int
    :param rowCount: Number of rows in the uploaded data
    :type rowCount: Optional[int]
    :param dataSchema: Schema definition for the uploaded data
    :type dataSchema: Dict[str, str]
    :param uploadedAt: When the upload was initiated
    :type uploadedAt: datetime
    :param processedAt: When processing was completed
    :type processedAt: Optional[datetime]
    :param errorDetails: List of errors encountered during processing
    :type errorDetails: Optional[List[Dict[str, Any]]]
    """

    uploadId: str = Field(..., description="Upload ID")
    instanceId: str = Field(..., description="AMC instance ID")
    datasetName: str = Field(..., description="Dataset name")
    uploadStatus: str = Field(..., description="Upload status")
    fileSize: int = Field(..., description="File size in bytes")
    rowCount: Optional[int] = Field(None, description="Number of rows")
    dataSchema: Dict[str, str] = Field(
        ...,
        alias="schema",
        serialization_alias="schema",
        description="Data schema",
    )
    uploadedAt: datetime = Field(..., description="Upload timestamp")
    processedAt: Optional[datetime] = Field(
        None, description="Processing completion timestamp"
    )
    errorDetails: Optional[List[Dict[str, Any]]] = Field(
        None, description="Upload errors"
    )


class AMCDataUploadRequest(BaseAMCModel):
    """Request to upload data to AMC.

    Contains all parameters needed to upload data to
    Amazon Marketing Cloud.

    :param datasetName: Name for the new dataset
    :type datasetName: str
    :param dataSchema: Schema definition for the data
    :type dataSchema: Dict[str, str]
    :param fileUrl: S3 URL of the data file to upload
    :type fileUrl: str
    :param fileFormat: Format of the data file
    :type fileFormat: str
    :param compressionType: Type of compression used (if any)
    :type compressionType: Optional[str]
    :param hasHeader: Whether the file has a header row
    :type hasHeader: bool
    :param delimiter: Field delimiter for CSV files
    :type delimiter: Optional[str]
    """

    datasetName: str = Field(..., description="Dataset name")
    dataSchema: Dict[str, str] = Field(
        ...,
        alias="schema",
        serialization_alias="schema",
        description="Data schema",
    )
    fileUrl: str = Field(..., description="S3 URL of data file")
    fileFormat: str = Field(..., description="File format (CSV, JSON, etc)")
    compressionType: Optional[str] = Field(None, description="Compression type")
    hasHeader: bool = Field(True, description="File has header row")
    delimiter: Optional[str] = Field(",", description="Field delimiter for CSV")


# Template Models
class AMCQueryTemplate(BaseAMCModel):
    """AMC query template model.

    Represents a reusable query template with parameterized
    SQL and example usage.

    :param templateId: Unique identifier for the template
    :type templateId: str
    :param templateName: Human-readable name for the template
    :type templateName: str
    :param category: Category or grouping for the template
    :type category: str
    :param description: Detailed description of the template
    :type description: str
    :param templateQuery: SQL template with parameter placeholders
    :type templateQuery: str
    :param requiredParameters: List of required parameters
    :type requiredParameters: List[str]
    :param optionalParameters: List of optional parameters
    :type optionalParameters: List[str]
    :param outputSchema: Expected structure of query results
    :type outputSchema: Dict[str, str]
    :param exampleParameters: Example values for parameters
    :type exampleParameters: Dict[str, Any]
    :param tags: List of tags for categorization
    :type tags: List[str]
    :param isOfficial: Whether this is an Amazon-provided template
    :type isOfficial: bool
    """

    templateId: str = Field(..., description="Template ID")
    templateName: str = Field(..., description="Template name")
    category: str = Field(..., description="Template category")
    description: str = Field(..., description="Template description")
    templateQuery: str = Field(..., description="Template SQL with placeholders")
    requiredParameters: List[str] = Field(..., description="Required parameters")
    optionalParameters: List[str] = Field(
        default_factory=list, description="Optional parameters"
    )
    outputSchema: Dict[str, str] = Field(..., description="Expected output schema")
    exampleParameters: Dict[str, Any] = Field(
        ..., description="Example parameter values"
    )
    tags: List[str] = Field(default_factory=list, description="Template tags")
    isOfficial: bool = Field(False, description="Is Amazon official template")


class AMCQueryTemplateListResponse(BaseAMCModel):
    """Response for AMC query template list operations.

    Contains a list of AMC query templates with categorization.

    :param templates: List of AMC query templates
    :type templates: List[AMCQueryTemplate]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param categories: List of available template categories
    :type categories: List[str]
    """

    templates: List[AMCQueryTemplate] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    categories: List[str] = Field(
        default_factory=list, description="Available categories"
    )


# Insights Models
class AMCInsight(BaseAMCModel):
    """AMC automated insight model.

    Represents an automated insight generated by Amazon Marketing Cloud
    with recommendations and supporting data.

    :param insightId: Unique identifier for the insight
    :type insightId: str
    :param instanceId: AMC instance where insight was generated
    :type instanceId: str
    :param insightType: Category or type of insight
    :type insightType: str
    :param title: Human-readable title for the insight
    :type title: str
    :param description: Detailed description of the insight
    :type description: str
    :param significance: Importance level of the insight
    :type significance: str
    :param metrics: Key performance metrics supporting the insight
    :type metrics: Dict[str, Any]
    :param recommendations: List of actionable recommendations
    :type recommendations: List[str]
    :param supportingData: Additional data supporting the insight
    :type supportingData: Dict[str, Any]
    :param generatedAt: When the insight was generated
    :type generatedAt: datetime
    :param expiresAt: When the insight expires
    :type expiresAt: datetime
    """

    insightId: str = Field(..., description="Insight ID")
    instanceId: str = Field(..., description="AMC instance ID")
    insightType: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    significance: str = Field(..., description="Significance level (HIGH, MEDIUM, LOW)")
    metrics: Dict[str, Any] = Field(..., description="Key metrics")
    recommendations: List[str] = Field(..., description="Action recommendations")
    supportingData: Dict[str, Any] = Field(..., description="Supporting data")
    generatedAt: datetime = Field(..., description="Generation timestamp")
    expiresAt: datetime = Field(..., description="Expiration timestamp")


class AMCInsightListResponse(BaseAMCModel):
    """Response for AMC insight list operations.

    Contains a list of AMC insights with pagination support.

    :param insights: List of AMC insights
    :type insights: List[AMCInsight]
    :param nextToken: Token for retrieving the next page of results
    :type nextToken: Optional[str]
    :param totalResults: Total number of insights available
    :type totalResults: Optional[int]
    """

    insights: List[AMCInsight] = Field(default_factory=list)
    nextToken: Optional[str] = Field(None)
    totalResults: Optional[int] = Field(None)


# Privacy and Compliance Models
class AMCPrivacyConfig(BaseAMCModel):
    """AMC privacy configuration model.

    Represents privacy and compliance settings for an AMC instance
    including differential privacy and data retention policies.

    :param instanceId: AMC instance this configuration applies to
    :type instanceId: str
    :param privacyLevel: Overall privacy protection level
    :type privacyLevel: AMCPrivacyLevel
    :param minimumAggregationThreshold: Minimum group size for results
    :type minimumAggregationThreshold: int
    :param differentialPrivacyEnabled: Whether differential privacy is enabled
    :type differentialPrivacyEnabled: bool
    :param noiseLevel: Amount of noise added for differential privacy
    :type noiseLevel: Optional[float]
    :param suppressedDimensions: Dimensions that are suppressed for privacy
    :type suppressedDimensions: List[str]
    :param dataRetentionDays: How long data is retained
    :type dataRetentionDays: int
    :param allowedDataSources: Data sources that are permitted
    :type allowedDataSources: List[AMCDataSource]
    :param blockedDataSources: Data sources that are blocked
    :type blockedDataSources: List[AMCDataSource]
    """

    instanceId: str = Field(..., description="AMC instance ID")
    privacyLevel: AMCPrivacyLevel = Field(..., description="Privacy level")
    minimumAggregationThreshold: int = Field(
        ..., description="Minimum aggregation threshold"
    )
    differentialPrivacyEnabled: bool = Field(
        ..., description="Differential privacy enabled"
    )
    noiseLevel: Optional[float] = Field(
        None, description="Noise level for differential privacy"
    )
    suppressedDimensions: List[str] = Field(
        default_factory=list, description="Suppressed dimensions"
    )
    dataRetentionDays: int = Field(..., description="Data retention period in days")
    allowedDataSources: List[AMCDataSource] = Field(
        ..., description="Allowed data sources"
    )
    blockedDataSources: List[AMCDataSource] = Field(
        default_factory=list, description="Blocked data sources"
    )


# Workflow Models
class AMCWorkflow(BaseAMCModel):
    """AMC workflow model for automated query execution.

    Represents an automated workflow that executes queries on a schedule
    with multiple steps and error handling.

    :param workflowId: Unique identifier for the workflow
    :type workflowId: str
    :param workflowName: Human-readable name for the workflow
    :type workflowName: str
    :param instanceId: AMC instance where workflow is defined
    :type instanceId: str
    :param description: Optional description of the workflow
    :type description: Optional[str]
    :param steps: List of workflow execution steps
    :type steps: List[Dict[str, Any]]
    :param schedule: Cron expression for execution schedule
    :type schedule: Optional[str]
    :param isActive: Whether the workflow is currently active
    :type isActive: bool
    :param lastExecutionTime: When the workflow was last executed
    :type lastExecutionTime: Optional[datetime]
    :param nextExecutionTime: When the workflow will next execute
    :type nextExecutionTime: Optional[datetime]
    :param createdAt: When the workflow was created
    :type createdAt: datetime
    :param updatedAt: When the workflow was last updated
    :type updatedAt: datetime
    """

    workflowId: str = Field(..., description="Workflow ID")
    workflowName: str = Field(..., description="Workflow name")
    instanceId: str = Field(..., description="AMC instance ID")
    description: Optional[str] = Field(None, description="Workflow description")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")
    schedule: Optional[str] = Field(None, description="Execution schedule (cron)")
    isActive: bool = Field(True, description="Is workflow active")
    lastExecutionTime: Optional[datetime] = Field(
        None, description="Last execution timestamp"
    )
    nextExecutionTime: Optional[datetime] = Field(
        None, description="Next scheduled execution"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class AMCWorkflowExecution(BaseAMCModel):
    """AMC workflow execution model.

    Represents a single execution of an AMC workflow with
    step results and error handling.

    :param executionId: Unique identifier for the execution
    :type executionId: str
    :param workflowId: ID of the workflow that was executed
    :type workflowId: str
    :param status: Current status of the execution
    :type status: AMCQueryStatus
    :param startTime: When execution began
    :type startTime: datetime
    :param endTime: When execution completed (if finished)
    :type endTime: Optional[datetime]
    :param stepResults: Results for each workflow step
    :type stepResults: List[Dict[str, Any]]
    :param errorDetails: Error details if execution failed
    :type errorDetails: Optional[Dict[str, Any]]
    """

    executionId: str = Field(..., description="Execution ID")
    workflowId: str = Field(..., description="Workflow ID")
    status: AMCQueryStatus = Field(..., description="Execution status")
    startTime: datetime = Field(..., description="Start time")
    endTime: Optional[datetime] = Field(None, description="End time")
    stepResults: List[Dict[str, Any]] = Field(..., description="Results for each step")
    errorDetails: Optional[Dict[str, Any]] = Field(
        None, description="Error details if failed"
    )


# Export all models
__all__ = [
    # Enums
    "AMCQueryStatus",
    "AMCQueryType",
    "AMCDataSource",
    "AMCAudienceStatus",
    "AMCPrivacyLevel",
    "AMCExportFormat",
    "AMCInstanceType",
    # Instance models
    "AMCInstance",
    "AMCInstanceListResponse",
    # Query models
    "AMCQuery",
    "AMCQueryExecution",
    "AMCQueryExecutionRequest",
    "AMCQueryListResponse",
    # Audience models
    "AMCAudience",
    "AMCAudienceCreateRequest",
    "AMCAudienceListResponse",
    # Data upload models
    "AMCDataUpload",
    "AMCDataUploadRequest",
    # Template models
    "AMCQueryTemplate",
    "AMCQueryTemplateListResponse",
    # Insight models
    "AMCInsight",
    "AMCInsightListResponse",
    # Privacy models
    "AMCPrivacyConfig",
    # Workflow models
    "AMCWorkflow",
    "AMCWorkflowExecution",
]
