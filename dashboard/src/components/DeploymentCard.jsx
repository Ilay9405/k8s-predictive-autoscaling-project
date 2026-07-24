// dashboard/src/components/DeploymentCard.jsx
import React, { useState, useEffect } from 'react';
import PodChart from './PodChart';

function DeploymentCard({ name, info }) {
    const pods = Object.entries(info.pods || {});
    
    // Default to the first pod in the list
    const [selectedPodName, setSelectedPodName] = useState('');

    useEffect(() => {
        if (pods.length > 0 && !pods.find(([podName]) => podName === selectedPodName)) {
            setSelectedPodName(pods[0][0]);
        }
    }, [pods, selectedPodName]);

    // We look at the first pod's recommendation for the big numbers, since all pods in a deployment
    // share the same recommendation in our backend architecture.
    const firstPod = pods.length > 0 ? pods[0][1] : null;
    const selectedPodInfo = info.pods[selectedPodName] || null;

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
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '1rem', margin: 0, color: 'var(--text-secondary)' }}>AI Pod Predictions</h3>
                    {pods.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {pods.map(([podName]) => {
                                const isSelected = podName === selectedPodName;
                                return (
                                    <button
                                        key={podName}
                                        onClick={() => setSelectedPodName(podName)}
                                        style={{
                                            background: isSelected ? 'var(--accent-blue)' : 'rgba(255,255,255,0.05)',
                                            color: isSelected ? '#fff' : 'var(--text-secondary)',
                                            border: `1px solid ${isSelected ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)'}`,
                                            padding: '6px 14px',
                                            borderRadius: '20px',
                                            cursor: 'pointer',
                                            fontSize: '0.8rem',
                                            transition: 'all 0.2s ease',
                                            boxShadow: isSelected ? '0 0 10px rgba(0, 168, 255, 0.4)' : 'none'
                                        }}
                                    >
                                        {podName.split('-').slice(-2).join('-')} {/* Just show the hash part for cleaner UI */}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>
                
                {selectedPodName && selectedPodInfo ? (
                    <PodChart podName={selectedPodName} podInfo={selectedPodInfo} />
                ) : (
                    <div style={{ padding: '24px', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '12px' }}>
                        <p style={{ color: 'var(--text-secondary)' }}>Waiting for pods to collect 46 minutes of historical data...</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default DeploymentCard;

