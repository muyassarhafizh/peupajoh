export class ApiError extends Error {
  code: number;
  errors: any | undefined;

  constructor(code: number, message: string, errors?: any | undefined) {
    super(message);
    this.code = code;
    this.errors = errors;
  }
}