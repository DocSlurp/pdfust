export * from './native'

/** Error thrown by every binding call; `code` is one of the codes below. */
export declare class PdfustError extends Error {
  /**
   * `PDF_LOCKED` (password needed or wrong), `PDF_LIMIT` (see `limit`), `PDF_ERROR`,
   * `INVALID_ARGUMENT`, `PDF_CLOSED`, or `NATIVE_PDF_UNSUPPORTED`.
   */
  code: string
  limit?: string
}

/** Thrown with code `NATIVE_PDF_UNSUPPORTED` for methods this binding cannot serve. */
export declare class NotImplementedError extends PdfustError {
  code: 'NATIVE_PDF_UNSUPPORTED'
}
