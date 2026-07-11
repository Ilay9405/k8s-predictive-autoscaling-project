// dashboard/src/components/PodChart.jsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

function PodChart({ podName, podInfo }) {
    // Format the raw backend data into something Recharts understands easily
    const data = podInfo.predictions.map(pred => {
        const date = new Date(pred.time);
        return {
            time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            cpu: parseFloat(pred.cpu.toFixed(3))
        };
    });

    return (
        <div style={{ marginBottom: '24px' }}>
            <div style={{ marginBottom: '8px', fontSize: '0.875rem' }}>
                Pod: <strong style={{ color: '#fff' }}>{podName}</strong>
            </div>

            <div style={{ height: '200px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />

                        <XAxis
                            dataKey="time"
                            stroke="var(--text-secondary)"
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            tickMargin={10}
                        />
                        <YAxis
                            stroke="var(--text-secondary)"
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        />

                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--bg-secondary)',
                                borderColor: 'var(--border-color)',
                                borderRadius: '8px'
                            }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                        />

                        {/* The dotted threshold line showing our exact scaling trigger! */}
                        <ReferenceLine
                            y={podInfo.target_cores}
                            stroke="var(--accent-purple)"
                            strokeDasharray="3 3"
                            label={{ position: 'top', value: 'Threshold', fill: 'var(--accent-purple)', fontSize: 12 }}
                        />

                        {/* The glowing AI prediction line */}
                        <Line
                            type="monotone"
                            dataKey="cpu"
                            stroke="var(--accent-blue)"
                            strokeWidth={3}
                            dot={false}
                            activeDot={{ r: 6, fill: 'var(--accent-blue)', stroke: '#fff' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default PodChart;
