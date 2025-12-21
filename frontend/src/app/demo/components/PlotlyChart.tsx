import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import Plotly from 'plotly.js-finance-dist';
import createPlotlyComponent from 'react-plotly.js/factory';

// Create Plot component with finance distribution
const Plot = createPlotlyComponent(Plotly);

interface CandlestickChartProps {
    data: any;
    range: string;
    ticker: string;
}

export function CandlestickChart({ data, range, ticker }: CandlestickChartProps) {
    if (!data || !data[range]) {
        return (
            <div className="h-[400px] flex items-center justify-center text-gray-500 bg-[#0a0e14] rounded-lg">
                <span>No data available for {range}</span>
            </div>
        );
    }

    const periodData = data[range];
    const { timestamps, opens, highs, lows, closes, volumes } = periodData;

    if (!timestamps || timestamps.length === 0) {
        return (
            <div className="h-[400px] flex items-center justify-center text-gray-500 bg-[#0a0e14] rounded-lg">
                <span>Insufficient data</span>
            </div>
        );
    }

    // Convert timestamps to dates
    const dates = useMemo(() => timestamps.map((ts: number) => new Date(ts * 1000)), [timestamps]);

    const chartData = useMemo(() => [
        {
            x: dates,
            open: opens,
            high: highs,
            low: lows,
            close: closes,
            type: 'candlestick',
            name: ticker,
            increasing: { line: { color: '#26a69a' } },
            decreasing: { line: { color: '#ef5350' } },
            hoverlabel: {
                bgcolor: '#1a1a1a',
                bordercolor: '#26a69a',
                font: { color: '#ffffff', size: 12 }
            }
        }
    ], [dates, opens, highs, lows, closes, ticker]);

    const volumeData = useMemo(() => volumes ? [{
        x: dates,
        y: volumes,
        type: 'bar',
        name: 'Volume',
        marker: {
            color: volumes.map((_: any, i: number) => closes[i] >= opens[i] ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)')
        },
        yaxis: 'y2',
        hovertemplate: 'Volume: %{y:,.0f}<extra></extra>'
    }] : [], [dates, volumes, closes, opens]);

    const layout = useMemo(() => ({
        autosize: true,
        height: 450,
        plot_bgcolor: '#0a0e14',
        paper_bgcolor: '#0a0e14',
        font: { color: '#9ca3af', size: 11 },
        margin: { l: 60, r: 40, t: 40, b: 40 },
        xaxis: {
            gridcolor: '#1f2937',
            showgrid: true,
            rangeslider: { visible: false },
            type: 'date',
            tickformat: range === '1d' ? '%H:%M' : range === '5d' ? '%b %d' : '%b %Y'
        },
        yaxis: {
            gridcolor: '#1f2937',
            showgrid: true,
            domain: [0.25, 1],
            title: { text: 'Price (INR)', font: { size: 11 } },
            tickprefix: '₹'
        },
        yaxis2: {
            domain: [0, 0.2],
            showgrid: false,
            title: { text: 'Volume', font: { size: 10 } }
        },
        hovermode: 'x unified',
        dragmode: 'zoom',
        showlegend: false
    }), [range]);

    const config = useMemo(() => ({
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        modeBarButtonsToAdd: [],
        responsive: true,
        toImageButtonOptions: {
            format: 'png',
            filename: `${ticker}_${range}`,
            height: 800,
            width: 1400,
            scale: 2
        }
    }), [ticker, range]);

    return (
        <div className="w-full bg-[#0a0e14] rounded-lg p-2">
            <Plot
                data={[...chartData, ...volumeData]}
                layout={layout}
                config={config}
                className="w-full"
                useResizeHandler
                style={{ width: '100%', height: '450px' }}
            />
        </div>
    );
}
