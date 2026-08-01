// dashboard/src/components/DeploymentChart.jsx
import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart
} from 'recharts';

function DeploymentChart({ history, predictions, targetCores, currentReplicas, recommendedReplicas }) {
    // Build the unified CPU chart data: historical (solid) + predicted (dashed)
    const historyData = (history || []).map(point => ({
        time: new Date(point.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        actual: parseFloat(point.cpu.toFixed(4)),
        predicted: null,
    }));

    const predictionData = (predictions || []).map(point => ({
        time: new Date(point.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        actual: null,
        predicted: parseFloat(point.cpu.toFixed(4)),
    }));

    // Connect the two lines: bridge the last history point into predictions
    if (historyData.length > 0 && predictionData.length > 0) {
        predictionData[0].actual = historyData[historyData.length - 1].actual;
    }

    const chartData = [...historyData, ...predictionData];

    // Thin out the X-axis labels so they don't overlap
    const totalPoints = chartData.length;
    const tickInterval = Math.max(1, Math.floor(totalPoints / 8));

    return (
        <div className="chart-section">
            {/* CPU Load Graph */}
            <div className="chart-container">
                <h3 className="chart-title">
                    <span className="chart-icon">📊</span>
                    Aggregate CPU Load
                    {predictions && predictions.length > 0 && (
                        <span className="prediction-badge">+ AI Forecast</span>
                    )}
                </h3>
                <div style={{ height: '260px', width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                            <defs>
                                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="predGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent-purple)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--accent-purple)" stopOpacity={0} />
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

                            <Tooltip content={<CpuTooltip targetCores={targetCores} />} />

                            {/* Threshold reference line */}
                            <ReferenceLine
                                y={targetCores}
                                stroke="var(--accent-purple)"
                                strokeDasharray="6 4"
                                strokeWidth={1.5}
                                label={{
                                    position: 'right',
                                    value: `Threshold: ${targetCores?.toFixed(3)}`,
                                    fill: 'var(--accent-purple)',
                                    fontSize: 11
                                }}
                            />

                            {/* Historical CPU — solid blue line with gradient fill */}
                            <Area
                                type="monotone"
                                dataKey="actual"
                                stroke="var(--accent-blue)"
                                strokeWidth={2}
                                fill="url(#cpuGradient)"
                                dot={false}
                                activeDot={{ r: 5, fill: 'var(--accent-blue)', stroke: '#fff', strokeWidth: 2 }}
                                connectNulls={false}
                            />

                            {/* Predicted CPU — dashed purple line with gradient fill */}
                            <Area
                                type="monotone"
                                dataKey="predicted"
                                stroke="var(--accent-purple)"
                                strokeWidth={2.5}
                                strokeDasharray="8 4"
                                fill="url(#predGradient)"
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
                        Historical CPU
                    </div>
                    <div className="legend-item">
                        <span className="legend-line purple dashed"></span>
                        AI Prediction
                    </div>
                    <div className="legend-item">
                        <span className="legend-line purple dotted"></span>
                        Scaling Threshold
                    </div>
                </div>
            </div>
        </div>
    );
}

// Custom tooltip for the CPU graph
function CpuTooltip({ active, payload, label, targetCores }) {
    if (!active || !payload || !payload.length) return null;

    const actualVal = payload.find(p => p.dataKey === 'actual');
    const predictedVal = payload.find(p => p.dataKey === 'predicted');

    return (
        <div className="custom-tooltip">
            <p className="tooltip-time">{label}</p>
            {actualVal && actualVal.value !== null && (
                <p className="tooltip-row blue">
                    Actual CPU: <strong>{actualVal.value.toFixed(4)} cores</strong>
                </p>
            )}
            {predictedVal && predictedVal.value !== null && (
                <p className="tooltip-row purple">
                    Predicted CPU: <strong>{predictedVal.value.toFixed(4)} cores</strong>
                </p>
            )}
            {targetCores && (
                <p className="tooltip-row dim">
                    Threshold: {targetCores.toFixed(4)} cores
                </p>
            )}
        </div>
    );
}

export default DeploymentChart;
