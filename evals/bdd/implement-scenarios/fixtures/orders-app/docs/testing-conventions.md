# Testing conventions

- Unit tests live in `tests/unit`. Service tests live in `tests/service`. End-to-end tests live in
  `tests/e2e`.
- Add no new test runner and no new dependency to `package.json`.
- A service test starts its own dependencies. An end-to-end test drives the storefront in a browser.
