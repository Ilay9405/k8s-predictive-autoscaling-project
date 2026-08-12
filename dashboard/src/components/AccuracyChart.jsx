import React from 'react';
import {
    XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Area, ComposedChart, Line
} from 'recharts';

function AccuracyChart({ data, horizonMinutes }) {
    // Format the time strings to local time for the chart
    const chartData = (data || []).map(point => ({
        ...point,
        time: new Date(point.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    }));

    // Thin out the X-axis labels so they don't overlap
    const totalPoints = chartData.length;
    const tickInterval = Math.max(1, Math.floor(totalPoints / 8));

    return (
        <div className="chart-section">
            <div className="chart-container">
                <h3 className="chart-title">
                    <span className="chart-icon">🎯</span>
                    Accuracy: {horizonMinutes}-Minute Forecast vs Reality
                </h3>
                <div style={{ height: '260px', width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: -10, bottom: 5 }}>
                            <defs>
                                <linearGradient id="accCpuGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                                </linearGradient>
                            </defs>

                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />

                            <XAxis
                                dataKey="time"
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                                tickMargin={10}
                                interval={tickInterval}
                                angle={-30}
                                textAnchor="end"
                                height={50}
                            />
                            <YAxis
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                                tickFormatter={(v) => v.toFixed(2)}
                            />

                            <Tooltip content={<AccuracyTooltip />} />

                            {/* Actual CPU — solid blue area */}
                            <Area
                                type="monotone"
                                dataKey="actual"
                                stroke="var(--accent-blue)"
                                strokeWidth={2}
                                fill="url(#accCpuGradient)"
                                dot={false}
                                activeDot={{ r: 5, fill: 'var(--accent-blue)', stroke: '#fff', strokeWidth: 2 }}
                                connectNulls={false}
                            />

                            {/* Predicted CPU (Historical) — dashed purple line overlaid */}
                            <Line
                                type="monotone"
                                dataKey="predicted"
                                stroke="var(--accent-purple)"
                                strokeWidth={2.5}
                                strokeDasharray="8 4"
                                dot={false}
                                activeDot={{ r: 5, fill: 'var(--accent-purple)', stroke: '#fff', strokeWidth: 2 }}
                                connectNulls={false}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="chart-legend">
                    <div className="legend-item">
                        <span className="legend-line blue"></span>
                        Actual CPU
                    </div>
                    <div className="legend-item">
                        <span className="legend-line purple dashed"></span>
                        AI Prediction (From {horizonMinutes}m ago)
                    </div>
                </div>
            </div>
        </div>
    );
}

// Custom tooltip to show the exact error delta!
function AccuracyTooltip({ active, payload, label }) {
    if (!active || !payload || !payload.length) return null;

    const actualVal = payload.find(p => p.dataKey === 'actual');
    const predictedVal = payload.find(p => p.dataKey === 'predicted');

    // Calculate delta (error margin)
    let errorText = null;
    let errorColor = "dim";
    if (actualVal && actualVal.value !== null && predictedVal && predictedVal.value !== null) {
        const diff = predictedVal.value - actualVal.value;
        const absDiff = Math.abs(diff);
        const symbol = diff > 0 ? "+" : "-";
        
        // If error is large (e.g., > 1.0 core off), highlight it in red/warning
        if (absDiff > 1.0) errorColor = "var(--text-primary)";
        
        errorText = `Delta: ${symbol}${absDiff.toFixed(3)} cores`;
    }

    return (
        <div className="custom-tooltip">
            <p className="tooltip-time">{label}</p>
            {actualVal && actualVal.value !== null && (
                <p className="tooltip-row blue">
                    Actual: <strong>{actualVal.value.toFixed(4)} cores</strong>
                </p>
            )}
            {predictedVal && predictedVal.value !== null && (
                <p className="tooltip-row purple">
                    Predicted: <strong>{predictedVal.value.toFixed(4)} cores</strong>
                </p>
            )}
            {errorText && (
                <p className="tooltip-row" style={{ color: errorColor, marginTop: '4px', fontStyle: 'italic' }}>
                    {errorText}
                </p>
            )}
        </div>
    );
}

export default AccuracyChart;
