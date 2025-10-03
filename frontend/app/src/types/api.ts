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
 * RegisteredTask
 * Model for registered Celery tasks.
 */
export interface RegisteredTask {
  /** Name */
  name: string;
  /** Doc */
  doc?: string | null;
  /** Full Name */
  full_name?: string | null;
  /** Module */
  module?: string | null;
}

/**
 * TaskEventResponse
 * Pydantic model for API responses
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
  /** Retry Of */
  retry_of?: string | null;
  /** Retried By */
  retried_by?: string[];
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
  /**
   * Orphaned At
   * @format date-time
   */
  orphaned_at?: string | null;
}

/**
 * TaskStats
 * Task statistics model
 */
export interface TaskStats {
  /**
   * Total Tasks
   * @default 0
   */
  total_tasks?: number;
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
   * Active
   * @default 0
   */
  active?: number;
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
     * @description Get current task statistics.
     *
     * @tags tasks
     * @name GetTaskStatsApiStatsGet
     * @summary Get Task Stats
     * @request GET:/api/stats
     */
    getTaskStatsApiStatsGet: (params: RequestParams = {}) =>
      this.request<TaskStats, any>({
        path: `/api/stats`,
        method: "GET",
        format: "json",
        ...params,
      }),

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
     * @description Get tasks that have been marked as orphaned.
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
     * @description Get all registered Celery tasks with their documentation.
     *
     * @tags registry
     * @name GetRegisteredTasksApiRegistryTasksGet
     * @summary Get Registered Tasks
     * @request GET:/api/registry/tasks
     */
    getRegisteredTasksApiRegistryTasksGet: (params: RequestParams = {}) =>
      this.request<RegisteredTask[], any>({
        path: `/api/registry/tasks`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * @description Get detailed information about a specific registered task.
     *
     * @tags registry
     * @name GetTaskDetailsApiRegistryTasksTaskNameGet
     * @summary Get Task Details
     * @request GET:/api/registry/tasks/{task_name}
     */
    getTaskDetailsApiRegistryTasksTaskNameGet: (
      taskName: string,
      params: RequestParams = {},
    ) =>
      this.request<object, HTTPValidationError>({
        path: `/api/registry/tasks/${taskName}`,
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
