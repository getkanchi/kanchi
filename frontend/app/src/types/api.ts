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
 * TaskEventResponse
 * Pydantic model for API responses with nested retry relationships
 */
export interface TaskEventResponse {
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
  /**
   * Args
   * @default "()"
   */
  args?: string;
  /**
   * Kwargs
   * @default "{}"
   */
  kwargs?: string;
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
  /**
   * Exchange
   * @default ""
   */
  exchange?: string;
  /**
   * Routing Key
   * @default ""
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
  retry_of?: TaskEventResponse | null;
  /** Retried By */
  retried_by?: TaskEventResponse[];
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
     * @description Get recent task events with filtering and pagination. Filters can be provided in two ways: 1. New format: filters="state:is:success,worker:contains:celery@host" 2. Legacy format: filter_state=success&filter_worker=celery (deprecated) Filter syntax: field:operator:value(s) - Fields: state, worker, task, queue, id - Operators: is, not, in, not_in, contains, starts - Multiple values: comma-separated for in/not_in operators
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
      this.request<TaskEventResponse[], HTTPValidationError>({
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
      this.request<TaskEventResponse[], any>({
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
      this.request<TaskEventResponse[], any>({
        path: `/api/tasks/orphaned`,
        method: "GET",
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
     * @description Get all unique tags across all tasks.
     *
     * @tags registry
     * @name GetAllTagsApiRegistryTagsGet
     * @summary Get All Tags
     * @request GET:/api/registry/tags
     */
    getAllTagsApiRegistryTagsGet: (params: RequestParams = {}) =>
      this.request<string[], any>({
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
     * @description Health check endpoint.
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
  };
}
