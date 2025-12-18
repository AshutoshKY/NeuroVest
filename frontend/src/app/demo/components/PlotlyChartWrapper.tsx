// Wrapper to dynamically load PlotlyChart only on client side
import dynamic from 'next/dynamic';

// Import with no SSR to prevent "self is not defined" error
export const CandlestickChart = dynamic(
    () => import('./PlotlyChart').then(mod => mod.CandlestickChart),
    {
        ssr: false,
        loading: () => <div>Loading chart...</div>
    }
);
