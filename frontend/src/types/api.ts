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



import { HttpClient, RequestParams, ContentType, HttpResponse } from "./http-client";
import { HTTPValidationError, TaskEventResponse, TaskStats, ValidationError } from "./data-contracts"

export class Api<SecurityDataType = unknown> extends HttpClient<SecurityDataType>  {

            /**
 * @description Get current task statistics
 *
 * @name GetTaskStatsApiStatsGet
 * @summary Get Task Stats
 * @request GET:/api/stats
 */
getTaskStatsApiStatsGet: (params: RequestParams = {}) =>
    this.request<TaskStats, any>({
        path: `/api/stats`,
        method: 'GET',
                                        format: "json",        ...params,
    }),            /**
 * @description Get recent task events
 *
 * @name GetRecentEventsApiEventsRecentGet
 * @summary Get Recent Events
 * @request GET:/api/events/recent
 */
getRecentEventsApiEventsRecentGet: (query?: {
  /**
   * Limit
   * @default 100
   */
    limit?: number,

}, params: RequestParams = {}) =>
    this.request<(TaskEventResponse)[], HTTPValidationError>({
        path: `/api/events/recent`,
        method: 'GET',
        query: query,                                format: "json",        ...params,
    }),            /**
 * @description Get events for a specific task
 *
 * @name GetTaskEventsApiEventsTaskIdGet
 * @summary Get Task Events
 * @request GET:/api/events/{task_id}
 */
getTaskEventsApiEventsTaskIdGet: (taskId: string, params: RequestParams = {}) =>
    this.request<(TaskEventResponse)[], HTTPValidationError>({
        path: `/api/events/${taskId}`,
        method: 'GET',
                                        format: "json",        ...params,
    }),            /**
 * @description Get currently active tasks
 *
 * @name GetActiveTasksApiTasksActiveGet
 * @summary Get Active Tasks
 * @request GET:/api/tasks/active
 */
getActiveTasksApiTasksActiveGet: (params: RequestParams = {}) =>
    this.request<(TaskEventResponse)[], any>({
        path: `/api/tasks/active`,
        method: 'GET',
                                        format: "json",        ...params,
    }),            /**
 * @description Health check endpoint
 *
 * @name HealthCheckApiHealthGet
 * @summary Health Check
 * @request GET:/api/health
 */
healthCheckApiHealthGet: (params: RequestParams = {}) =>
    this.request<any, any>({
        path: `/api/health`,
        method: 'GET',
                                        format: "json",        ...params,
    }),    }
