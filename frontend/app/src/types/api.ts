/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/**
 * ConditionOperator
 * Supported condition operators.
 */
export enum ConditionOperator {
  Equals = "equals",
  NotEquals = "not_equals",
  In = "in",
  NotIn = "not_in",
  Matches = "matches",
  Gt = "gt",
  Lt = "lt",
  Gte = "gte",
  Lte = "lte",
  Contains = "contains",
  StartsWith = "starts_with",
  EndsWith = "ends_with",
}

/**
 * ActionConfig
 * Configuration for a single action.
 */
export interface ActionConfig {
  /** Type */
  type: string;
  /** Config Id */
  config_id?: string | null;
  /** Params */
  params?: object;
  /**
   * Continue On Failure
   * @default true
   */
  continue_on_failure?: boolean;
}

/**
 * ActionConfigCreateRequest
 * Request model for creating action config.
 */
export interface ActionConfigCreateRequest {
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /** Action Type */
  action_type: string;
  /** Config */
  config: object;
}

/**
 * ActionConfigDefinition
 * Reusable action configuration.
 */
export interface ActionConfigDefinition {
  /** Id */
  id?: string | null;
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /** Action Type */
  action_type: string;
  /** Config */
  config: object;
  /** Created At */
  created_at?: string | null;
  /** Updated At */
  updated_at?: string | null;
  /** Created By */
  created_by?: string | null;
  /**
   * Usage Count
   * @default 0
   */
  usage_count?: number;
  /** Last Used At */
  last_used_at?: string | null;
}

/**
 * ActionConfigUpdateRequest
 * Request model for updating action config.
 */
export interface ActionConfigUpdateRequest {
  /** Name */
  name?: string | null;
  /** Description */
  description?: string | null;
  /** Config */
  config?: object | null;
}

/**
 * AuthConfigResponse
 * Backend authentication configuration.
 */
export interface AuthConfigResponse {
  /** Auth Enabled */
  auth_enabled: boolean;
  /** Basic Enabled */
  basic_enabled: boolean;
  /** Oauth Providers */
  oauth_providers?: string[];
  /** Allowed Email Patterns */
  allowed_email_patterns?: string[];
}

/**
 * AuthTokens
 * Token bundle returned after login/refresh.
 */
export interface AuthTokens {
  /** Access Token */
  access_token: string;
  /** Refresh Token */
  refresh_token: string;
  /**
   * Token Type
   * @default "bearer"
   */
  token_type?: "bearer";
  /** Expires In */
  expires_in: number;
  /** Refresh Expires In */
  refresh_expires_in: number;
  /** Session Id */
  session_id: string;
}

/**
 * BasicLoginRequest
 * Basic authentication request payload.
 */
export interface BasicLoginRequest {
  /** Username */
  username: string;
  /** Password */
  password: string;
  /** Session Id */
  session_id?: string | null;
}

/**
 * CircuitBreakerConfig
 * Configuration for workflow-level circuit breaking.
 */
export interface CircuitBreakerConfig {
  /**
   * Enabled
   * @default true
   */
  enabled?: boolean;
  /**
   * Max Executions
   * Number of executions allowed per window
   * @min 1
   * @default 1
   */
  max_executions?: number;
  /**
   * Window Seconds
   * Sliding window size in seconds
   * @min 1
   * @default 300
   */
  window_seconds?: number;
  /**
   * Context Field
   * Event context field used to group executions (e.g., root_id, task_id)
   */
  context_field?: string | null;
}

/**
 * Condition
 * Single condition for workflow filtering.
 */
export interface Condition {
  /** Field */
  field: string;
  /** Supported condition operators. */
  operator: ConditionOperator;
  /** Value */
  value: any;
}

/**
 * ConditionGroup
 * Group of conditions with AND/OR logic.
 */
export interface ConditionGroupInput {
  /**
   * Operator
   * @default "AND"
   */
  operator?: "AND" | "OR";
  /** Conditions */
  conditions?: Condition[];
}

/**
 * ConditionGroup
 * Group of conditions with AND/OR logic.
 */
export interface ConditionGroupOutput {
  /**
   * Operator
   * @default "AND"
   */
  operator?: "AND" | "OR";
  /** Conditions */
  conditions?: Condition[];
}

/**
 * EnvironmentCreate
 * Environment creation request model
 */
export interface EnvironmentCreate {
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /** Queue Patterns */
  queue_patterns?: string[];
  /** Worker Patterns */
  worker_patterns?: string[];
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
}

/**
 * EnvironmentResponse
 * Environment API response model
 */
export interface EnvironmentResponse {
  /** Id */
  id: string;
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /** Queue Patterns */
  queue_patterns?: string[];
  /** Worker Patterns */
  worker_patterns?: string[];
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Updated At
   * @format date-time
   */
  updated_at: string;
}

/**
 * EnvironmentUpdate
 * Environment update request model
 */
export interface EnvironmentUpdate {
  /** Name */
  name?: string | null;
  /** Description */
  description?: string | null;
  /** Queue Patterns */
  queue_patterns?: string[] | null;
  /** Worker Patterns */
  worker_patterns?: string[] | null;
  /** Is Default */
  is_default?: boolean | null;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * LogEntry
 * Log entry from frontend
 */
export interface LogEntry {
  /** Level */
  level: string;
  /** Message */
  message: string;
  /** Timestamp */
  timestamp?: string | null;
  /** Context */
  context?: object | null;
}

/**
 * LoginResponse
 * Login response payload.
 */
export interface LoginResponse {
  /** Authenticated user information returned to clients. */
  user: UserInfo;
  /** Token bundle returned after login/refresh. */
  tokens: AuthTokens;
  /** Provider */
  provider: string;
}

/**
 * LogoutRequest
 * Logout request payload.
 */
export interface LogoutRequest {
  /** Session Id */
  session_id?: string | null;
}

/**
 * RefreshRequest
 * Refresh token request payload.
 */
export interface RefreshRequest {
  /** Refresh Token */
  refresh_token: string;
}

/**
 * TaskDailyStatsResponse
 * Daily statistics response model
 */
export interface TaskDailyStatsResponse {
  /** Task Name */
  task_name: string;
  /**
   * Date
   * @format date
   */
  date: string;
  /**
   * Total Executions
   * @default 0
   */
  total_executions?: number;
  /**
   * Succeeded
   * @default 0
   */
  succeeded?: number;
  /**
   * Failed
   * @default 0
   */
  failed?: number;
  /**
   * Pending
   * @default 0
   */
  pending?: number;
  /**
   * Retried
   * @default 0
   */
  retried?: number;
  /**
   * Revoked
   * @default 0
   */
  revoked?: number;
  /**
   * Orphaned
   * @default 0
   */
  orphaned?: number;
  /** Avg Runtime */
  avg_runtime?: number | null;
  /** Min Runtime */
  min_runtime?: number | null;
  /** Max Runtime */
  max_runtime?: number | null;
  /** P50 Runtime */
  p50_runtime?: number | null;
  /** P95 Runtime */
  p95_runtime?: number | null;
  /** P99 Runtime */
  p99_runtime?: number | null;
  /** First Execution */
  first_execution?: string | null;
  /** Last Execution */
  last_execution?: string | null;
}

/**
 * TaskEvent
 * Represents a Celery task event
 */
export interface TaskEvent {
  /** Task Id */
  task_id: string;
  /** Task Name */
  task_name: string;
  /** Event Type */
  event_type: string;
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
  /** Args */
  args?: any[];
  /** Kwargs */
  kwargs?: object;
  /**
   * Retries
   * @default 0
   */
  retries?: number;
  /** Eta */
  eta?: string | null;
  /** Expires */
  expires?: string | null;
  /** Hostname */
  hostname?: string | null;
  /** Worker Name */
  worker_name?: string | null;
  /** Queue */
  queue?: string | null;
  /**
   * Exchange
   * @default ""
   */
  exchange?: string;
  /**
   * Routing Key
   * @default "default"
   */
  routing_key?: string;
  /** Root Id */
  root_id?: string | null;
  /** Parent Id */
  parent_id?: string | null;
  /** Result */
  result?: null;
  /** Runtime */
  runtime?: number | null;
  /** Exception */
  exception?: string | null;
  /** Traceback */
  traceback?: string | null;
  retry_of?: TaskEvent | null;
  /** Retried By */
  retried_by?: TaskEvent[];
  /**
   * Is Retry
   * @default false
   */
  is_retry?: boolean;
  /**
   * Has Retries
   * @default false
   */
  has_retries?: boolean;
  /**
   * Retry Count
   * @default 0
   */
  retry_count?: number;
  /**
   * Is Orphan
   * @default false
   */
  is_orphan?: boolean;
  /** Orphaned At */
  orphaned_at?: string | null;
}

/**
 * TaskRegistryResponse
 * Task registry API response model
 */
export interface TaskRegistryResponse {
  /** Id */
  id: string;
  /** Name */
  name: string;
  /** Human Readable Name */
  human_readable_name?: string | null;
  /** Description */
  description?: string | null;
  /** Tags */
  tags?: string[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Updated At
   * @format date-time
   */
  updated_at: string;
  /**
   * First Seen
   * @format date-time
   */
  first_seen: string;
  /**
   * Last Seen
   * @format date-time
   */
  last_seen: string;
}

/**
 * TaskRegistryStats
 * Statistics for a specific task
 */
export interface TaskRegistryStats {
  /** Task Name */
  task_name: string;
  /**
   * Total Executions
   * @default 0
   */
  total_executions?: number;
  /**
   * Succeeded
   * @default 0
   */
  succeeded?: number;
  /**
   * Failed
   * @default 0
   */
  failed?: number;
  /**
   * Pending
   * @default 0
   */
  pending?: number;
  /**
   * Retried
   * @default 0
   */
  retried?: number;
  /** Avg Runtime */
  avg_runtime?: number | null;
  /** Last Execution */
  last_execution?: string | null;
}

/**
 * TaskRegistryUpdate
 * Task registry update request model
 */
export interface TaskRegistryUpdate {
  /** Human Readable Name */
  human_readable_name?: string | null;
  /** Description */
  description?: string | null;
  /** Tags */
  tags?: string[] | null;
}

/**
 * TaskTimelineResponse
 * Timeline response showing execution frequency over time
 */
export interface TaskTimelineResponse {
  /** Task Name */
  task_name: string;
  /**
   * Start Time
   * @format date-time
   */
  start_time: string;
  /**
   * End Time
   * @format date-time
   */
  end_time: string;
  /** Bucket Size Minutes */
  bucket_size_minutes: number;
  /** Buckets */
  buckets: TimelineBucket[];
}

/**
 * TimelineBucket
 * Single time bucket in timeline
 */
export interface TimelineBucket {
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
  /**
   * Total Executions
   * @default 0
   */
  total_executions?: number;
  /**
   * Succeeded
   * @default 0
   */
  succeeded?: number;
  /**
   * Failed
   * @default 0
   */
  failed?: number;
  /**
   * Retried
   * @default 0
   */
  retried?: number;
}

/**
 * TriggerConfig
 * Base trigger configuration.
 */
export interface TriggerConfig {
  /** Type */
  type: string;
  /** Config */
  config?: object;
}

/**
 * UserInfo
 * Authenticated user information returned to clients.
 */
export interface UserInfo {
  /** Id */
  id: string;
  /** Email */
  email: string;
  /** Provider */
  provider: string;
  /** Name */
  name?: string | null;
  /** Avatar Url */
  avatar_url?: string | null;
}

/**
 * UserSessionResponse
 * User session API response model
 */
export interface UserSessionResponse {
  /** Session Id */
  session_id: string;
  /** Active Environment Id */
  active_environment_id?: string | null;
  /** Preferences */
  preferences?: object;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Last Active
   * @format date-time
   */
  last_active: string;
}

/**
 * UserSessionUpdate
 * User session update request model
 */
export interface UserSessionUpdate {
  /** Active Environment Id */
  active_environment_id?: string | null;
  /** Preferences */
  preferences?: object | null;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
}

/**
 * WorkerInfo
 * Worker information model
 */
export interface WorkerInfo {
  /** Hostname */
  hostname: string;
  /** Status */
  status: string;
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
  /**
   * Active Tasks
   * @default 0
   */
  active_tasks?: number;
  /**
   * Processed Tasks
   * @default 0
   */
  processed_tasks?: number;
  /** Sw Ident */
  sw_ident?: string | null;
  /** Sw Ver */
  sw_ver?: string | null;
  /** Sw Sys */
  sw_sys?: string | null;
  /** Loadavg */
  loadavg?: number[] | null;
  /** Freq */
  freq?: number | null;
}

/**
 * WorkflowCreateRequest
 * Request model for creating a workflow.
 */
export interface WorkflowCreateRequest {
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /**
   * Enabled
   * @default true
   */
  enabled?: boolean;
  /** Base trigger configuration. */
  trigger: TriggerConfig;
  conditions?: ConditionGroupInput | null;
  /** Actions */
  actions: ActionConfig[];
  /**
   * Priority
   * @default 100
   */
  priority?: number;
  /** Max Executions Per Hour */
  max_executions_per_hour?: number | null;
  /**
   * Cooldown Seconds
   * @default 0
   */
  cooldown_seconds?: number;
  circuit_breaker?: CircuitBreakerConfig | null;
}

/**
 * WorkflowDefinition
 * Complete workflow definition.
 */
export interface WorkflowDefinition {
  /** Id */
  id?: string | null;
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /**
   * Enabled
   * @default true
   */
  enabled?: boolean;
  /** Base trigger configuration. */
  trigger: TriggerConfig;
  conditions?: ConditionGroupOutput | null;
  /** Actions */
  actions: ActionConfig[];
  /**
   * Priority
   * @default 100
   */
  priority?: number;
  /** Max Executions Per Hour */
  max_executions_per_hour?: number | null;
  /**
   * Cooldown Seconds
   * @default 0
   */
  cooldown_seconds?: number;
  circuit_breaker?: CircuitBreakerConfig | null;
  /** Created At */
  created_at?: string | null;
  /** Updated At */
  updated_at?: string | null;
  /** Created By */
  created_by?: string | null;
  /**
   * Execution Count
   * @default 0
   */
  execution_count?: number;
  /** Last Executed At */
  last_executed_at?: string | null;
  /**
   * Success Count
   * @default 0
   */
  success_count?: number;
  /**
   * Failure Count
   * @default 0
   */
  failure_count?: number;
}

/**
 * WorkflowExecutionRecord
 * Execution history record.
 */
export interface WorkflowExecutionRecord {
  /** Id */
  id: number;
  /** Workflow Id */
  workflow_id: string;
  /**
   * Triggered At
   * @format date-time
   */
  triggered_at: string;
  /** Trigger Type */
  trigger_type: string;
  /** Trigger Event */
  trigger_event: object;
  /** Status */
  status:
    | "pending"
    | "running"
    | "completed"
    | "failed"
    | "rate_limited"
    | "circuit_open";
  /** Actions Executed */
  actions_executed?: object[] | null;
  /** Error Message */
  error_message?: string | null;
  /** Stack Trace */
  stack_trace?: string | null;
  /** Started At */
  started_at?: string | null;
  /** Completed At */
  completed_at?: string | null;
  /** Duration Ms */
  duration_ms?: number | null;
  /** Workflow Snapshot */
  workflow_snapshot?: object | null;
  /** Circuit Breaker Key */
  circuit_breaker_key?: string | null;
}

/**
 * WorkflowUpdateRequest
 * Request model for updating a workflow.
 */
export interface WorkflowUpdateRequest {
  /** Name */
  name?: string | null;
  /** Description */
  description?: string | null;
  /** Enabled */
  enabled?: boolean | null;
  trigger?: TriggerConfig | null;
  conditions?: ConditionGroupInput | null;
  /** Actions */
  actions?: ActionConfig[] | null;
  /** Priority */
  priority?: number | null;
  /** Max Executions Per Hour */
  max_executions_per_hour?: number | null;
  /** Cooldown Seconds */
  cooldown_seconds?: number | null;
  circuit_breaker?: CircuitBreakerConfig | null;
}

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  HeadersDefaults,
  ResponseType,
} from "axios";
import axios from "axios";

export type QueryParamsType = Record<string | number, any>;

export interface FullRequestParams
  extends Omit<AxiosRequestConfig, "data" | "params" | "url" | "responseType"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseType;
  /** request body */
  body?: unknown;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown>
  extends Omit<AxiosRequestConfig, "data" | "cancelToken"> {
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<AxiosRequestConfig | void> | AxiosRequestConfig | void;
  secure?: boolean;
  format?: ResponseType;
}

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public instance: AxiosInstance;
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private secure?: boolean;
  private format?: ResponseType;

  constructor({
    securityWorker,
    secure,
    format,
    ...axiosConfig
  }: ApiConfig<SecurityDataType> = {}) {
    this.instance = axios.create({
      ...axiosConfig,
      baseURL: axiosConfig.baseURL || "",
    });
    this.secure = secure;
    this.format = format;
    this.securityWorker = securityWorker;
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected mergeRequestParams(
    params1: AxiosRequestConfig,
    params2?: AxiosRequestConfig,
  ): AxiosRequestConfig {
    const method = params1.method || (params2 && params2.method);

    return {
      ...this.instance.defaults,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...((method &&
          this.instance.defaults.headers[
            method.toLowerCase() as keyof HeadersDefaults
          ]) ||
          {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected stringifyFormItem(formItem: unknown) {
    if (typeof formItem === "object" && formItem !== null) {
      return JSON.stringify(formItem);
    } else {
      return `${formItem}`;
    }
  }

  protected createFormData(input: Record<string, unknown>): FormData {
    if (input instanceof FormData) {
      return input;
    }
    return Object.keys(input || {}).reduce((formData, key) => {
      const property = input[key];
      const propertyContent: any[] =
        property instanceof Array ? property : [property];

      for (const formItem of propertyContent) {
        const isFileType = formItem instanceof Blob || formItem instanceof File;
        formData.append(
          key,
          isFileType ? formItem : this.stringifyFormItem(formItem),
        );
      }

      return formData;
    }, new FormData());
  }

  public request = async <T = any, _E = any>({
    secure,
    path,
    type,
    query,
    format,
    body,
    ...params
  }: FullRequestParams): Promise<AxiosResponse<T>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const responseFormat = format || this.format || undefined;

    if (
      type === ContentType.FormData &&
      body &&
      body !== null &&
      typeof body === "object"
    ) {
      body = this.createFormData(body as Record<string, unknown>);
    }

    if (
      type === ContentType.Text &&
      body &&
      body !== null &&
      typeof body !== "string"
    ) {
      body = JSON.stringify(body);
    }

    return this.instance.request({
      ...requestParams,
      headers: {
        ...(requestParams.headers || {}),
        ...(type ? { "Content-Type": type } : {}),
      },
      params: query,
      responseType: responseFormat,
      data: body,
      url: path,
    });
  };
}

/**
 * @title Celery Event Monitor
 * @version 0.1.0
 *
 * Real-time monitoring of Celery task events with WebSocket broadcasting
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  api = {
    /**
     * @description Get recent task events with filtering and pagination.
     *
     * @tags tasks
     * @name GetRecentEventsApiEventsRecentGet
     * @summary Get Recent Events
     * @request GET:/api/events/recent
     */
    getRecentEventsApiEventsRecentGet: (
      query?: {
        /**
         * Limit
         * @default 100
         */
        limit?: number;
        /**
         * Page
         * @default 0
         */
        page?: number;
        /**
         * Aggregate
         * @default true
         */
        aggregate?: boolean;
        /** Sort By */
        sort_by?: string | null;
        /**
         * Sort Order
         * @default "desc"
         */
        sort_order?: string;
        /** Search */
        search?: string | null;
        /** Filters */
        filters?: string | null;
        /** Start Time */
        start_time?: string | null;
        /** End Time */
        end_time?: string | null;
        /** Filter State */
        filter_state?: string | null;
        /** Filter Worker */
        filter_worker?: string | null;
        /** Filter Task */
        filter_task?: string | null;
        /** Filter Queue */
        filter_queue?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<object, HTTPValidationError>({
        path: `/api/events/recent`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get all events for a specific task.
     *
     * @tags tasks
     * @name GetTaskEventsApiEventsTaskIdGet
     * @summary Get Task Events
     * @request GET:/api/events/{task_id}
     */
    getTaskEventsApiEventsTaskIdGet: (
      taskId: string,
      params: RequestParams = {},
    ) =>
      this.request<TaskEvent[], HTTPValidationError>({
        path: `/api/events/${taskId}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get currently active tasks.
     *
     * @tags tasks
     * @name GetActiveTasksApiTasksActiveGet
     * @summary Get Active Tasks
     * @request GET:/api/tasks/active
     */
    getActiveTasksApiTasksActiveGet: (params: RequestParams = {}) =>
      this.request<TaskEvent[], HTTPValidationError>({
        path: `/api/tasks/active`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get tasks that have been marked as orphaned and NOT yet retried.
     *
     * @tags tasks
     * @name GetOrphanedTasksApiTasksOrphanedGet
     * @summary Get Orphaned Tasks
     * @request GET:/api/tasks/orphaned
     */
    getOrphanedTasksApiTasksOrphanedGet: (params: RequestParams = {}) =>
      this.request<TaskEvent[], HTTPValidationError>({
        path: `/api/tasks/orphaned`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get failed tasks within the last ``hours`` window.
     *
     * @tags tasks
     * @name GetRecentFailedTasksApiTasksFailedRecentGet
     * @summary Get Recent Failed Tasks
     * @request GET:/api/tasks/failed/recent
     */
    getRecentFailedTasksApiTasksFailedRecentGet: (
      query?: {
        /**
         * Hours
         * @default 24
         */
        hours?: number;
        /**
         * Limit
         * @default 50
         */
        limit?: number;
        /**
         * Include Retried
         * @default false
         */
        include_retried?: boolean;
      },
      params: RequestParams = {},
    ) =>
      this.request<TaskEvent[], HTTPValidationError>({
        path: `/api/tasks/failed/recent`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Retry a failed task by creating a new task with the same parameters.
     *
     * @tags tasks
     * @name RetryTaskApiTasksTaskIdRetryPost
     * @summary Retry Task
     * @request POST:/api/tasks/{task_id}/retry
     */
    retryTaskApiTasksTaskIdRetryPost: (
      taskId: string,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/tasks/${taskId}/retry`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * @description Get information about all workers.
     *
     * @tags workers
     * @name GetWorkersApiWorkersGet
     * @summary Get Workers
     * @request GET:/api/workers
     */
    getWorkersApiWorkersGet: (params: RequestParams = {}) =>
      this.request<WorkerInfo[], any>({
        path: `/api/workers`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get information about a specific worker.
     *
     * @tags workers
     * @name GetWorkerApiWorkersHostnameGet
     * @summary Get Worker
     * @request GET:/api/workers/{hostname}
     */
    getWorkerApiWorkersHostnameGet: (
      hostname: string,
      params: RequestParams = {},
    ) =>
      this.request<WorkerInfo, HTTPValidationError>({
        path: `/api/workers/${hostname}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get recent worker events.
     *
     * @tags workers
     * @name GetRecentWorkerEventsApiWorkersEventsRecentGet
     * @summary Get Recent Worker Events
     * @request GET:/api/workers/events/recent
     */
    getRecentWorkerEventsApiWorkersEventsRecentGet: (
      query?: {
        /**
         * Limit
         * @default 50
         */
        limit?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/workers/events/recent`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get schema information for WebSocket message types.
     *
     * @tags websocket
     * @name GetWebsocketMessageTypesApiWebsocketMessageTypesGet
     * @summary Get Websocket Message Types
     * @request GET:/api/websocket/message-types
     */
    getWebsocketMessageTypesApiWebsocketMessageTypesGet: (
      params: RequestParams = {},
    ) =>
      this.request<any, any>({
        path: `/api/websocket/message-types`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Receive log messages from frontend and write to unified log file (only in development mode).
     *
     * @tags logs
     * @name LogFrontendMessageApiLogsFrontendPost
     * @summary Log Frontend Message
     * @request POST:/api/logs/frontend
     */
    logFrontendMessageApiLogsFrontendPost: (
      data: LogEntry,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/logs/frontend`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description List all registered tasks with optional filters. Args: tag: Filter by tag (case-insensitive partial match) name: Filter by task name (case-insensitive partial match)
     *
     * @tags registry
     * @name ListTasksApiRegistryTasksGet
     * @summary List Tasks
     * @request GET:/api/registry/tasks
     */
    listTasksApiRegistryTasksGet: (
      query?: {
        /** Tag */
        tag?: string | null;
        /** Name */
        name?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<TaskRegistryResponse[], HTTPValidationError>({
        path: `/api/registry/tasks`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get details about a specific task. Args: task_name: The name of the task to retrieve
     *
     * @tags registry
     * @name GetTaskApiRegistryTasksTaskNameGet
     * @summary Get Task
     * @request GET:/api/registry/tasks/{task_name}
     */
    getTaskApiRegistryTasksTaskNameGet: (
      taskName: string,
      params: RequestParams = {},
    ) =>
      this.request<TaskRegistryResponse, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Update task metadata (human_readable_name, description, tags). Args: task_name: The name of the task to update update_data: The fields to update
     *
     * @tags registry
     * @name UpdateTaskApiRegistryTasksTaskNamePut
     * @summary Update Task
     * @request PUT:/api/registry/tasks/{task_name}
     */
    updateTaskApiRegistryTasksTaskNamePut: (
      taskName: string,
      data: TaskRegistryUpdate,
      params: RequestParams = {},
    ) =>
      this.request<TaskRegistryResponse, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}`,
        method: "PUT",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Get statistics for a specific task. Args: task_name: The name of the task hours: Number of hours to look back (default: 24)
     *
     * @tags registry
     * @name GetTaskStatsApiRegistryTasksTaskNameStatsGet
     * @summary Get Task Stats
     * @request GET:/api/registry/tasks/{task_name}/stats
     */
    getTaskStatsApiRegistryTasksTaskNameStatsGet: (
      taskName: string,
      query?: {
        /**
         * Hours
         * @default 24
         */
        hours?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<TaskRegistryStats, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}/stats`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get execution timeline for visualizing task frequency over time. Args: task_name: The name of the task hours: Number of hours to look back (default: 24) bucket_size_minutes: Size of each time bucket in minutes (default: 60)
     *
     * @tags registry
     * @name GetTaskTimelineApiRegistryTasksTaskNameTimelineGet
     * @summary Get Task Timeline
     * @request GET:/api/registry/tasks/{task_name}/timeline
     */
    getTaskTimelineApiRegistryTasksTaskNameTimelineGet: (
      taskName: string,
      query?: {
        /**
         * Hours
         * Number of hours to look back
         * @default 24
         */
        hours?: number;
        /**
         * Bucket Size Minutes
         * Bucket size in minutes (e.g., 60 for 1-hour buckets)
         * @default 60
         */
        bucket_size_minutes?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<TaskTimelineResponse, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}/timeline`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get all unique tags across all tasks.
     *
     * @tags registry
     * @name GetAllTagsApiRegistryTagsGet
     * @summary Get All Tags
     * @request GET:/api/registry/tags
     */
    getAllTagsApiRegistryTagsGet: (params: RequestParams = {}) =>
      this.request<string[], HTTPValidationError>({
        path: `/api/registry/tags`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get daily statistics for a task. Args: task_name: The name of the task start_date: Optional start date end_date: Optional end date days: Number of days to look back (default: 30, used if no dates specified)
     *
     * @tags registry
     * @name GetTaskDailyStatsApiRegistryTasksTaskNameDailyStatsGet
     * @summary Get Task Daily Stats
     * @request GET:/api/registry/tasks/{task_name}/daily-stats
     */
    getTaskDailyStatsApiRegistryTasksTaskNameDailyStatsGet: (
      taskName: string,
      query?: {
        /**
         * Start Date
         * Start date (YYYY-MM-DD)
         */
        start_date?: string | null;
        /**
         * End Date
         * End date (YYYY-MM-DD)
         */
        end_date?: string | null;
        /**
         * Days
         * Number of days to look back (if no dates specified)
         * @default 30
         */
        days?: number | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<TaskDailyStatsResponse[], HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}/daily-stats`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get trend summary for a task over the last N days. Returns: Summary with success rates, failure rates, and average runtime
     *
     * @tags registry
     * @name GetTaskTrendApiRegistryTasksTaskNameTrendGet
     * @summary Get Task Trend
     * @request GET:/api/registry/tasks/{task_name}/trend
     */
    getTaskTrendApiRegistryTasksTaskNameTrendGet: (
      taskName: string,
      query?: {
        /**
         * Days
         * Number of days to analyze
         * @default 7
         */
        days?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<object, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}/trend`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get statistics for all tasks on a specific date. Args: target_date: The date to get stats for (YYYY-MM-DD)
     *
     * @tags registry
     * @name GetAllTasksStatsForDateApiRegistryDailyStatsTargetDateGet
     * @summary Get All Tasks Stats For Date
     * @request GET:/api/registry/daily-stats/{target_date}
     */
    getAllTasksStatsForDateApiRegistryDailyStatsTargetDateGet: (
      targetDate: string,
      params: RequestParams = {},
    ) =>
      this.request<TaskDailyStatsResponse[], HTTPValidationError>({
        path: `/api/registry/daily-stats/${targetDate}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description List all environments.
     *
     * @tags environments
     * @name ListEnvironmentsApiEnvironmentsGet
     * @summary List Environments
     * @request GET:/api/environments
     */
    listEnvironmentsApiEnvironmentsGet: (params: RequestParams = {}) =>
      this.request<EnvironmentResponse[], any>({
        path: `/api/environments`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Create a new environment.
     *
     * @tags environments
     * @name CreateEnvironmentApiEnvironmentsPost
     * @summary Create Environment
     * @request POST:/api/environments
     */
    createEnvironmentApiEnvironmentsPost: (
      data: EnvironmentCreate,
      params: RequestParams = {},
    ) =>
      this.request<EnvironmentResponse, HTTPValidationError>({
        path: `/api/environments`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Get environment by ID.
     *
     * @tags environments
     * @name GetEnvironmentApiEnvironmentsEnvIdGet
     * @summary Get Environment
     * @request GET:/api/environments/{env_id}
     */
    getEnvironmentApiEnvironmentsEnvIdGet: (
      envId: string,
      params: RequestParams = {},
    ) =>
      this.request<EnvironmentResponse, HTTPValidationError>({
        path: `/api/environments/${envId}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Update an environment.
     *
     * @tags environments
     * @name UpdateEnvironmentApiEnvironmentsEnvIdPatch
     * @summary Update Environment
     * @request PATCH:/api/environments/{env_id}
     */
    updateEnvironmentApiEnvironmentsEnvIdPatch: (
      envId: string,
      data: EnvironmentUpdate,
      params: RequestParams = {},
    ) =>
      this.request<EnvironmentResponse, HTTPValidationError>({
        path: `/api/environments/${envId}`,
        method: "PATCH",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Delete an environment.
     *
     * @tags environments
     * @name DeleteEnvironmentApiEnvironmentsEnvIdDelete
     * @summary Delete Environment
     * @request DELETE:/api/environments/{env_id}
     */
    deleteEnvironmentApiEnvironmentsEnvIdDelete: (
      envId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/api/environments/${envId}`,
        method: "DELETE",
        ...params,
      }),

    /**
     * @description Initialize or retrieve a session. If session_id is provided in header, retrieves existing or creates new.
     *
     * @tags sessions
     * @name InitializeSessionApiSessionsInitPost
     * @summary Initialize Session
     * @request POST:/api/sessions/init
     */
    initializeSessionApiSessionsInitPost: (params: RequestParams = {}) =>
      this.request<UserSessionResponse, HTTPValidationError>({
        path: `/api/sessions/init`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * @description Get current session info.
     *
     * @tags sessions
     * @name GetCurrentSessionApiSessionsMeGet
     * @summary Get Current Session
     * @request GET:/api/sessions/me
     */
    getCurrentSessionApiSessionsMeGet: (params: RequestParams = {}) =>
      this.request<UserSessionResponse, HTTPValidationError>({
        path: `/api/sessions/me`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Update current session preferences.
     *
     * @tags sessions
     * @name UpdateCurrentSessionApiSessionsMePatch
     * @summary Update Current Session
     * @request PATCH:/api/sessions/me
     */
    updateCurrentSessionApiSessionsMePatch: (
      data: UserSessionUpdate,
      params: RequestParams = {},
    ) =>
      this.request<UserSessionResponse, HTTPValidationError>({
        path: `/api/sessions/me`,
        method: "PATCH",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Set active environment for current session.
     *
     * @tags sessions
     * @name SetSessionEnvironmentApiSessionsMeEnvironmentEnvironmentIdPost
     * @summary Set Session Environment
     * @request POST:/api/sessions/me/environment/{environment_id}
     */
    setSessionEnvironmentApiSessionsMeEnvironmentEnvironmentIdPost: (
      environmentId: string,
      params: RequestParams = {},
    ) =>
      this.request<UserSessionResponse, HTTPValidationError>({
        path: `/api/sessions/me/environment/${environmentId}`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * @description Clear active environment for current session (show all).
     *
     * @tags sessions
     * @name ClearSessionEnvironmentApiSessionsMeEnvironmentDelete
     * @summary Clear Session Environment
     * @request DELETE:/api/sessions/me/environment
     */
    clearSessionEnvironmentApiSessionsMeEnvironmentDelete: (
      params: RequestParams = {},
    ) =>
      this.request<UserSessionResponse, HTTPValidationError>({
        path: `/api/sessions/me/environment`,
        method: "DELETE",
        format: "json",
        ...params,
      }),

    /**
     * @description Expose supported triggers and actions.
     *
     * @tags workflows
     * @name GetWorkflowMetadataApiWorkflowsMetadataGet
     * @summary Get Workflow Metadata
     * @request GET:/api/workflows/metadata
     */
    getWorkflowMetadataApiWorkflowsMetadataGet: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/api/workflows/metadata`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Create a new workflow.
     *
     * @tags workflows
     * @name CreateWorkflowApiWorkflowsPost
     * @summary Create Workflow
     * @request POST:/api/workflows
     */
    createWorkflowApiWorkflowsPost: (
      data: WorkflowCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<WorkflowDefinition, HTTPValidationError>({
        path: `/api/workflows`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description List all workflows with optional filtering.
     *
     * @tags workflows
     * @name ListWorkflowsApiWorkflowsGet
     * @summary List Workflows
     * @request GET:/api/workflows
     */
    listWorkflowsApiWorkflowsGet: (
      query?: {
        /**
         * Enabled Only
         * @default false
         */
        enabled_only?: boolean;
        /** Trigger Type */
        trigger_type?: string | null;
        /**
         * Limit
         * @default 100
         */
        limit?: number;
        /**
         * Offset
         * @default 0
         */
        offset?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<WorkflowDefinition[], HTTPValidationError>({
        path: `/api/workflows`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get a specific workflow by ID.
     *
     * @tags workflows
     * @name GetWorkflowApiWorkflowsWorkflowIdGet
     * @summary Get Workflow
     * @request GET:/api/workflows/{workflow_id}
     */
    getWorkflowApiWorkflowsWorkflowIdGet: (
      workflowId: string,
      params: RequestParams = {},
    ) =>
      this.request<WorkflowDefinition, HTTPValidationError>({
        path: `/api/workflows/${workflowId}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Update an existing workflow.
     *
     * @tags workflows
     * @name UpdateWorkflowApiWorkflowsWorkflowIdPut
     * @summary Update Workflow
     * @request PUT:/api/workflows/{workflow_id}
     */
    updateWorkflowApiWorkflowsWorkflowIdPut: (
      workflowId: string,
      data: WorkflowUpdateRequest,
      params: RequestParams = {},
    ) =>
      this.request<WorkflowDefinition, HTTPValidationError>({
        path: `/api/workflows/${workflowId}`,
        method: "PUT",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Delete a workflow.
     *
     * @tags workflows
     * @name DeleteWorkflowApiWorkflowsWorkflowIdDelete
     * @summary Delete Workflow
     * @request DELETE:/api/workflows/{workflow_id}
     */
    deleteWorkflowApiWorkflowsWorkflowIdDelete: (
      workflowId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/api/workflows/${workflowId}`,
        method: "DELETE",
        ...params,
      }),

    /**
     * @description Get execution history for a workflow.
     *
     * @tags workflows
     * @name GetWorkflowExecutionsApiWorkflowsWorkflowIdExecutionsGet
     * @summary Get Workflow Executions
     * @request GET:/api/workflows/{workflow_id}/executions
     */
    getWorkflowExecutionsApiWorkflowsWorkflowIdExecutionsGet: (
      workflowId: string,
      query?: {
        /**
         * Limit
         * @default 100
         */
        limit?: number;
        /**
         * Offset
         * @default 0
         */
        offset?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<WorkflowExecutionRecord[], HTTPValidationError>({
        path: `/api/workflows/${workflowId}/executions`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get recent workflow executions across all workflows.
     *
     * @tags workflows
     * @name GetRecentExecutionsApiWorkflowsExecutionsRecentGet
     * @summary Get Recent Executions
     * @request GET:/api/workflows/executions/recent
     */
    getRecentExecutionsApiWorkflowsExecutionsRecentGet: (
      query?: {
        /** Status */
        status?: string | null;
        /**
         * Limit
         * @default 100
         */
        limit?: number;
        /**
         * Offset
         * @default 0
         */
        offset?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<WorkflowExecutionRecord[], HTTPValidationError>({
        path: `/api/workflows/executions/recent`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Test a workflow with sample data. This simulates workflow execution without actually triggering actions. Useful for debugging condition evaluation.
     *
     * @tags workflows
     * @name TestWorkflowApiWorkflowsWorkflowIdTestPost
     * @summary Test Workflow
     * @request POST:/api/workflows/{workflow_id}/test
     */
    testWorkflowApiWorkflowsWorkflowIdTestPost: (
      workflowId: string,
      data: object,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/workflows/${workflowId}/test`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Create a new action configuration (e.g., Slack webhook).
     *
     * @tags action-configs
     * @name CreateActionConfigApiActionConfigsPost
     * @summary Create Action Config
     * @request POST:/api/action-configs
     */
    createActionConfigApiActionConfigsPost: (
      data: ActionConfigCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<ActionConfigDefinition, HTTPValidationError>({
        path: `/api/action-configs`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description List all action configurations.
     *
     * @tags action-configs
     * @name ListActionConfigsApiActionConfigsGet
     * @summary List Action Configs
     * @request GET:/api/action-configs
     */
    listActionConfigsApiActionConfigsGet: (
      query?: {
        /** Action Type */
        action_type?: string | null;
        /**
         * Limit
         * @default 100
         */
        limit?: number;
        /**
         * Offset
         * @default 0
         */
        offset?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<ActionConfigDefinition[], HTTPValidationError>({
        path: `/api/action-configs`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Get a specific action configuration.
     *
     * @tags action-configs
     * @name GetActionConfigApiActionConfigsConfigIdGet
     * @summary Get Action Config
     * @request GET:/api/action-configs/{config_id}
     */
    getActionConfigApiActionConfigsConfigIdGet: (
      configId: string,
      params: RequestParams = {},
    ) =>
      this.request<ActionConfigDefinition, HTTPValidationError>({
        path: `/api/action-configs/${configId}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Update an action configuration.
     *
     * @tags action-configs
     * @name UpdateActionConfigApiActionConfigsConfigIdPut
     * @summary Update Action Config
     * @request PUT:/api/action-configs/{config_id}
     */
    updateActionConfigApiActionConfigsConfigIdPut: (
      configId: string,
      data: ActionConfigUpdateRequest,
      params: RequestParams = {},
    ) =>
      this.request<ActionConfigDefinition, HTTPValidationError>({
        path: `/api/action-configs/${configId}`,
        method: "PUT",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Delete an action configuration.
     *
     * @tags action-configs
     * @name DeleteActionConfigApiActionConfigsConfigIdDelete
     * @summary Delete Action Config
     * @request DELETE:/api/action-configs/{config_id}
     */
    deleteActionConfigApiActionConfigsConfigIdDelete: (
      configId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/api/action-configs/${configId}`,
        method: "DELETE",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name FetchAuthConfigApiAuthConfigGet
     * @summary Fetch Auth Config
     * @request GET:/api/auth/config
     */
    fetchAuthConfigApiAuthConfigGet: (params: RequestParams = {}) =>
      this.request<AuthConfigResponse, any>({
        path: `/api/auth/config`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name BasicLoginApiAuthBasicLoginPost
     * @summary Basic Login
     * @request POST:/api/auth/basic/login
     */
    basicLoginApiAuthBasicLoginPost: (
      data: BasicLoginRequest,
      params: RequestParams = {},
    ) =>
      this.request<LoginResponse, HTTPValidationError>({
        path: `/api/auth/basic/login`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name RefreshTokensApiAuthRefreshPost
     * @summary Refresh Tokens
     * @request POST:/api/auth/refresh
     */
    refreshTokensApiAuthRefreshPost: (
      data: RefreshRequest,
      params: RequestParams = {},
    ) =>
      this.request<LoginResponse, HTTPValidationError>({
        path: `/api/auth/refresh`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name LogoutApiAuthLogoutPost
     * @summary Logout
     * @request POST:/api/auth/logout
     */
    logoutApiAuthLogoutPost: (
      data: LogoutRequest,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/api/auth/logout`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name GetCurrentUserApiAuthMeGet
     * @summary Get Current User
     * @request GET:/api/auth/me
     */
    getCurrentUserApiAuthMeGet: (params: RequestParams = {}) =>
      this.request<UserInfo, any>({
        path: `/api/auth/me`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name OauthAuthorizeApiAuthOauthProviderAuthorizeGet
     * @summary Oauth Authorize
     * @request GET:/api/auth/oauth/{provider}/authorize
     */
    oauthAuthorizeApiAuthOauthProviderAuthorizeGet: (
      provider: string,
      query?: {
        /** Redirect To */
        redirect_to?: string | null;
        /** Session Id */
        session_id?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/auth/oauth/${provider}/authorize`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags auth
     * @name OauthCallbackApiAuthOauthProviderCallbackGet
     * @summary Oauth Callback
     * @request GET:/api/auth/oauth/{provider}/callback
     */
    oauthCallbackApiAuthOauthProviderCallbackGet: (
      provider: string,
      query?: {
        /** Code */
        code?: string | null;
        /** State */
        state?: string | null;
        /** Error */
        error?: string | null;
        /** Session Id */
        session_id?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/api/auth/oauth/${provider}/callback`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * @description Public health endpoint without sensitive data.
     *
     * @name HealthCheckApiHealthGet
     * @summary Health Check
     * @request GET:/api/health
     */
    healthCheckApiHealthGet: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/api/health`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Detailed health information (authentication required when enabled).
     *
     * @name HealthDetailsApiHealthDetailsGet
     * @summary Health Details
     * @request GET:/api/health/details
     */
    healthDetailsApiHealthDetailsGet: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/api/health/details`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
}
