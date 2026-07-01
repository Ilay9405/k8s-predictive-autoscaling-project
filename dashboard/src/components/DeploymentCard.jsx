// dashboard/src/components/DeploymentCard.jsx
import React from 'react';
import PodChart from './PodChart';

function DeploymentCard({ name, info }) {
    const pods = Object.entries(info.pods || {});

    // We look at the first pod's recommendation, since all pods in a deployment
    // share the same recommendation in our backend architecture.
    const firstPod = pods.length > 0 ? pods[0][1] : null;

    return (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* Header: Deployment Name and Target CPU */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ color: 'var(--accent-blue)', margin: 0 }}>{name}</h2>
                <span style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    padding: '4px 12px',
                    borderRadius: '99px',
                    fontSize: '0.875rem'
                }}>
                    Target CPU: {firstPod ? firstPod.target_cores.toFixed(2) : '0.00'} cores
                </span>
            </div>

            {/* The Big Numbers: Current vs Recommended */}
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '12px' }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Current Replicas</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{firstPod?.current_replicas || 0}</div>
                </div>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '12px' }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>AI Recommended</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-purple)' }}>
                        {firstPod?.recommended_replicas || 0}
                    </div>
                </div>
            </div>

            {/* The Graphs */}
            <div style={{ marginTop: '8px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>Pod Predictions</h3>
                {pods.map(([podName, podInfo]) => (
                    <PodChart key={podName} podName={podName} podInfo={podInfo} />
                ))}
                {pods.length === 0 && <p>No pod data available.</p>}
            </div>
        </div>
    );
}

export default DeploymentCard;
