
export function generateMockChartData() {
    const basePrice = 4284.25;
    return Array.from({ length: 50 }, (_, i) =>
        basePrice + (Math.random() - 0.5) * 100
    );
}
