import { ApiError } from "@/api/api.error";

interface ApiEnvelopeBase<T> {
  meta?: ApiError;
  data: T;
}

export type ApiEnvelope<T, P = undefined> = P extends undefined
  ? ApiEnvelopeBase<T> & { pagination?: undefined }
  : ApiEnvelopeBase<T> & { pagination: P };

export interface ApiPagination {
  // TODO: implement pagination
}