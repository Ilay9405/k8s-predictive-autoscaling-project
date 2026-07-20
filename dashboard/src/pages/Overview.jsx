// dashboard/src/pages/Overview.jsx
import React, { useEffect, useState } from 'react';
import DeploymentCard from '../components/DeploymentCard';

function Overview() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Poll the Python server every 5 seconds
        const fetchData = async () => {
            try {
                const response = await fetch('/api/status');
                const json = await response.json();
                setData(json);
                setError(null);
            } catch (err) {
                setError('Cannot connect to Inference Server. Is it running?');
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className="card" style={{ textAlign: 'center', marginTop: '2rem' }}>{error}</div>;
    }

    if (!data || data.status === 'initializing') {
        return <div style={{ textAlign: 'center', marginTop: '2rem' }}>Loading predictions...</div>;
    }

    const deployments = Object.entries(data.deployments || {});

    if (deployments.length === 0) {
        return <div className="card" style={{ textAlign: 'center', marginTop: '2rem' }}>No deployments found.</div>;
    }

    return (
        <div>
            <h1 style={{ textAlign: 'center', marginBottom: '10px' }}>Live ML Predictions</h1>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                Last Updated: {new Date(data.last_update).toLocaleTimeString()}
            </p>

            <div className="dashboard-grid">
                {deployments.map(([name, info]) => (
                    <DeploymentCard key={name} name={name} info={info} />
                ))}
            </div>
        </div>
    );
}

export default Overview;
