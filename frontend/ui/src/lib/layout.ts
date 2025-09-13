export function computeColumnWidth(
  containerWidth: number,
  gap: number,
  targetCols: number,
  minW: number,
  maxW: number
): number {
  const cols = Math.max(1, Math.floor(targetCols || 1))
  const totalGaps = gap * Math.max(0, cols - 1)
  const available = Math.max(0, containerWidth - totalGaps)
  if (available <= 0) return minW
  const w = Math.floor(available / cols)
  return Math.max(minW, Math.min(maxW, w))
}

// Sugestão de gap padrão (em px) para cada breakpoint Tailwind aproximado
export function defaultGapForWidth(containerWidth: number): number {
  if (containerWidth >= 1536) return 32 // 2xl
  if (containerWidth >= 1280) return 28 // xl
  if (containerWidth >= 1024) return 24 // lg
  if (containerWidth >= 768) return 20 // md
  return 16 // base/sm
}
