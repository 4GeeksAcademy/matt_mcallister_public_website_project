# TrackFlow Core (Milestone 2)

TypeScript business logic for TrackFlow inventory and carrier management.

## Scripts

- `npm run build`: compile TypeScript to `dist/`
- `npm run typecheck`: validate types without emit
- `npm run test`: run unit tests

## Modules

- `src/types/domain.ts`: domain interfaces and union types
- `src/utils/collections.ts`: filtering and sorting helpers
- `src/utils/search.ts`: linear and binary search helpers
- `src/utils/transformations.ts`: shipping cost, carrier scoring, and reporting
- `src/utils/validations.ts`: entity validators

## Notes

- Sorting helpers clone arrays before sorting to avoid mutating inputs.
- Numeric outputs for costs, averages, and scores are rounded to 2 decimals.
- `selectBestCarrier` keeps first-in-input selection for equal-cost ties.
