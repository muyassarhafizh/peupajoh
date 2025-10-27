import { ApiError } from './api.error';
import { ApiEnvelope } from '@/entities/api.entity';

export class ApiFactory {
  private baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  constructor() {
    if (!this.baseUrl) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL is not defined');
    }
  }

  protected async fetch<T, P = undefined>(
    relativeUrl: string,
    options: Omit<RequestInit, 'body'> & { body?: Record<string, any> | string | FormData } = {},
  ) {
    const url = new URL(relativeUrl, this.baseUrl);

    const headers = new Headers(options.headers);

    if (options.body && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
      options.body = JSON.stringify(options.body);
    }

    const requestOptions: RequestInit = {
      ...(options as RequestInit),
      headers,
    };

    const response = await fetch(url.toString(), requestOptions);

    const data = (await response.json()) as ApiEnvelope<T, P>;

    if (!response.ok) {
      if (data.meta) {
        throw new ApiError(data.meta.code, data.meta.message, data.meta.errors);
      } else {
        throw new Error(`Unknown error at api call on ${url.toString()}`);
      }
    }

    return data;
  }

  protected buildQuery(query?: Record<any, any>) {
    return Object.entries(query || {})
      .filter((item) => item[1])
      .map(([key, val]) => `${key}=${val}`)
      .join('&');
  }
}