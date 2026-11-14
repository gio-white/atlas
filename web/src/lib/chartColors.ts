// Chart colours, defined once (redesign brief §11). Charts take series colours in this fixed
// order and never cycle past the end; the app accent and the meaning colours stay out of
// charts. Class names are spelled out in full so Tailwind can see them.

export type SeriesColor = { stroke: string; swatch: string; fill: string }

export const SERIES: readonly SeriesColor[] = [
  { stroke: 'stroke-series-1', swatch: 'bg-series-1', fill: 'fill-series-1' },
  { stroke: 'stroke-series-2', swatch: 'bg-series-2', fill: 'fill-series-2' },
  { stroke: 'stroke-series-3', swatch: 'bg-series-3', fill: 'fill-series-3' },
  { stroke: 'stroke-series-4', swatch: 'bg-series-4', fill: 'fill-series-4' },
  { stroke: 'stroke-series-5', swatch: 'bg-series-5', fill: 'fill-series-5' },
  { stroke: 'stroke-series-6', swatch: 'bg-series-6', fill: 'fill-series-6' },
  { stroke: 'stroke-series-7', swatch: 'bg-series-7', fill: 'fill-series-7' },
  { stroke: 'stroke-series-8', swatch: 'bg-series-8', fill: 'fill-series-8' },
]

/** The colour for the slice at `index`; past the eighth, slices share a neutral "other" grey. */
export function seriesColor(index: number): SeriesColor {
  return SERIES[index] ?? OTHER
}

export const OTHER: SeriesColor = {
  stroke: 'stroke-data-neutral',
  swatch: 'bg-data-neutral',
  fill: 'fill-data-neutral',
}
