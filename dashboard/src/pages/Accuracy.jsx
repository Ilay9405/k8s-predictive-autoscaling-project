// dashboard/src/pages/Accuracy.jsx
import React, { useState, useEffect } from 'react';
import AccuracyChart from '../components/AccuracyChart';

function Accuracy() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [horizon, setHorizon] = useState(5); // Default to 5-minute forecast
    const [selectedDeployment, setSelectedDeployment] = useState("stressor-app");

    useEffect(() => {
        const fetchAccuracy = async () => {
            try {
                const response = await fetch(`/api/accuracy?horizon_minutes=${horizon}`);
                if (!response.ok) throw new Error('Network response was not ok');
                const json = await response.json();
                setData(json);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching accuracy data:", err);
                setError(err.message);
                setLoading(false);
            }
        };

        fetchAccuracy();
        const interval = setInterval(fetchAccuracy, 15000); // refresh every 15s
        return () => clearInterval(interval);
    }, [horizon]);

    if (loading && !data) return <div className="loading">Loading accuracy data...</div>;
    if (error) return <div className="error">Error: {error}</div>;
    
    // Pick the deployment data
    const deploymentData = data && data[selectedDeployment] ? data[selectedDeployment] : [];

    return (
        <div style={{ marginTop: '2rem' }}>
            <div className="header-row">
                <h2>Historical Accuracy</h2>
                <div className="controls">
                    <label style={{ marginRight: '10px', color: 'var(--text-secondary)' }}>Forecast Horizon:</label>
                    <select 
                        value={horizon} 
                        onChange={(e) => setHorizon(Number(e.target.value))}
                        style={{
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            padding: '5px 10px',
                            borderRadius: '4px'
                        }}
                    >
                        <option value={1}>1 Minute Ahead</option>
                        <option value={5}>5 Minutes Ahead</option>
                        <option value={10}>10 Minutes Ahead</option>
                        <option value={15}>15 Minutes Ahead</option>
                    </select>
                </div>
            </div>
            
            <p style={{ color: 'var(--text-secondary)', marginTop: '10px', marginBottom: '20px' }}>
                This graph overlays the AI's past predictions directly on top of the actual CPU load that occurred at that exact moment.
            </p>

            <div className="card">
                <AccuracyChart data={deploymentData} horizonMinutes={horizon} />
            </div>
        </div>
    );
}

export default Accuracy;
