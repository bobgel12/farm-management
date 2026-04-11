/** URL tab keys for house detail (order matches Tab panels when Water History is shown). */
export const HOUSE_TAB_KEYS = [
  'overview',
  'devices',
  'flock',
  'tasks',
  'messages',
  'mortality',
  'issues',
  'menu',
  'water-history',
] as const;

export type HouseTabKey = (typeof HOUSE_TAB_KEYS)[number];

export function tabKeyToIndex(key: string, hasWaterHistoryTab: boolean): number {
  const keys = hasWaterHistoryTab
    ? [...HOUSE_TAB_KEYS]
    : HOUSE_TAB_KEYS.filter((k) => k !== 'water-history');
  const idx = keys.indexOf(key as HouseTabKey);
  return idx >= 0 ? idx : 0;
}

export function indexToTabKey(index: number, hasWaterHistoryTab: boolean): string {
  const keys = hasWaterHistoryTab
    ? [...HOUSE_TAB_KEYS]
    : HOUSE_TAB_KEYS.filter((k) => k !== 'water-history');
  return keys[index] ?? 'overview';
}

export function overviewStorageKey(farmId: number): string {
  return `farm:${farmId}:overview`;
}

export function lastHouseStorageKey(farmId: number): string {
  return `farm:${farmId}:lastHouseId`;
}
