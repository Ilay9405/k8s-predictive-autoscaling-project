// dashboard/src/components/DeploymentCard.jsx
import React from 'react';
import DeploymentChart from './DeploymentChart';

function DeploymentCard({ name, info }) {
    const isCollecting = !info.predictions || info.predictions.length === 0;
    const progress = info.data_points && info.required_points
        ? Math.min(100, Math.round((info.data_points / info.required_points) * 100))
        : 0;

    return (
        <div className="card deployment-card">

            {/* Header: Deployment Name and Target CPU */}
            <div className="deployment-header">
                <h2 className="deployment-name">{name}</h2>
                <span className="target-badge">
                    Target CPU: {info.target_cores ? info.target_cores.toFixed(2) : '0.00'} cores
                </span>
            </div>

            {/* The Big Numbers: Current vs Recommended */}
            <div className="stats-row">
                <div className="stat-box">
                    <div className="stat-label">Current Replicas</div>
                    <div className="stat-value">{info.current_replicas || 0}</div>
                </div>
                <div className="stat-box">
                    <div className="stat-label">AI Recommended</div>
                    <div className="stat-value accent">
                        {info.recommended_replicas || 0}
                    </div>
                </div>
                <div className="stat-box">
                    <div className="stat-label">Live CPU</div>
                    <div className="stat-value small">{info.current_cpu ? info.current_cpu.toFixed(3) : '0.000'} cores</div>
                </div>
            </div>

            {/* Data Collection Progress or Chart */}
            {isCollecting ? (
                <div className="collecting-box">
                    <div className="collecting-header">
                        <span className="collecting-dot"></span>
                        <span>Collecting historical data...</span>
                    </div>
                    <div className="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p className="collecting-detail">
                        {info.data_points || 0} / {info.required_points || 185} data points ({progress}%)
                    </p>
                    {/* Still show the history graph even while collecting */}
                    {info.history && info.history.length > 5 && (
                        <DeploymentChart
                            history={info.history}
                            predictions={[]}
                            targetCores={info.target_cores}
                            currentReplicas={info.current_replicas}
                        />
                    )}
                </div>
            ) : (
                <DeploymentChart
                    history={info.history}
                    predictions={info.predictions}
                    targetCores={info.target_cores}
                    currentReplicas={info.current_replicas}
                    recommendedReplicas={info.recommended_replicas}
                />
            )}
        </div>
    );
}

export default DeploymentCard;
