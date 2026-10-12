'use strict'

// Thin wrapper over the generated loader (native.js). The native layer reports
// failures as "[CODE] message" (optionally "[CODE:limit] message"); this turns
// them into errors carrying `code` and `limit`, for sync calls and promises alike.

const native = require('./native.js')

class PdfustError extends Error {
  constructor(message, code, limit) {
    super(message)
    this.name = 'PdfustError'
    this.code = code
    if (limit) this.limit = limit
  }
}

class NotImplementedError extends PdfustError {
  constructor(message) {
    super(message, 'NATIVE_PDF_UNSUPPORTED')
    this.name = 'NotImplementedError'
  }
}

const PREFIX = /^\[([A-Z_]+)(?::([a-z_]+))?\] ([\s\S]*)$/

function normalize(error) {
  if (!(error instanceof Error)) return error
  const matched = PREFIX.exec(error.message)
  if (!matched) return error
  const [, code, limit, message] = matched
  const Type = code === 'NATIVE_PDF_UNSUPPORTED' ? NotImplementedError : PdfustError
  const wrapped = new Type(message, code, limit)
  wrapped.stack = error.stack
  return wrapped
}

function guard(fn) {
  return function guarded(...args) {
    let result
    try {
      result = fn.apply(this, args)
    } catch (error) {
      throw normalize(error)
    }
    if (result && typeof result.then === 'function') {
      return result.then(undefined, (error) => {
        throw normalize(error)
      })
    }
    return result
  }
}

function guardClass(Class) {
  for (const name of Object.getOwnPropertyNames(Class.prototype)) {
    if (name === 'constructor') continue
    const descriptor = Object.getOwnPropertyDescriptor(Class.prototype, name)
    if (typeof descriptor.value === 'function') {
      Object.defineProperty(Class.prototype, name, { ...descriptor, value: guard(descriptor.value) })
    }
  }
}

guardClass(native.PdfDoc)
guardClass(native.PdfPage)

module.exports = {
  PdfDoc: native.PdfDoc,
  PdfPage: native.PdfPage,
  PdfustError,
  NotImplementedError,
  version: guard(native.version),
  openPath: guard(native.openPath),
  openBuffer: guard(native.openBuffer),
}
