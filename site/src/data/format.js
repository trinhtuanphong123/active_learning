export function formatNumber(value, precision = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }

  const numericValue = Number(value);
  if (Math.abs(numericValue) >= 1000) {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(
      numericValue,
    );
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: precision,
    minimumFractionDigits: precision,
  }).format(numericValue);
}

export function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${Math.round(Number(value) * 100)}%`;
}
