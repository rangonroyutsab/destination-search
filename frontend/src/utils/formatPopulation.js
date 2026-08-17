export function formatPopulation(pop) {
  if (pop === null || pop === undefined) return 'Unknown population';
  if (pop >= 1000000) {
    return (pop / 1000000).toFixed(1).replace(/\.0$/, '') + 'M population';
  }
  if (pop >= 1000) {
    return Math.round(pop / 1000) + 'K population';
  }
  return pop.toLocaleString() + ' population';
}
