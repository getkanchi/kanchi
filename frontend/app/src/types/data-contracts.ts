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
