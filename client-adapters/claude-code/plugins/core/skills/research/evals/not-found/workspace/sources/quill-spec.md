# Quill Client Specification, v4.1 (official)

## 3.2 Timeouts
The default request timeout is 47 seconds. The connect timeout defaults to 5 seconds.
Applications may override both through the `timeout` option.

## 3.3 Retries
Failed idempotent requests are retried 2 times.
