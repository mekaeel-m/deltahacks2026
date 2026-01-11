import "../styles/PostureAnalysis.css";

export default function PostureAnalysis({ score, joints, error }) {
    return (
        <div className="settings-panel">
            <h2 className="settings-title">Posture Analysis</h2>

            {/* Overall Score Display */}
            <div className={`score-display ${score !== null ? (score >= 75 ? 'score-good' : score >= 50 ? 'score-warning' : 'score-bad') : 'score-neutral'}`}>
                <div className="score-ring">
                    <svg viewBox="0 0 100 100" className="score-svg">
                        <circle className="score-bg" cx="50" cy="50" r="42" />
                        <circle 
                            className="score-progress" 
                            cx="50" cy="50" r="42" 
                            style={{ 
                                strokeDasharray: `${(score || 0) * 2.64} 264`,
                                stroke: score !== null ? (score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444') : '#6b7280'
                            }}
                        />
                    </svg>
                    <div className="score-value">
                        <span className="score-number">{score !== null ? score.toFixed(1) : '--'}%</span>
                        <span className="score-label">Accuracy</span>
                    </div>
                </div>
            </div>
            
            {/* Joint Feedback Display */}
            {Object.keys(joints).length > 0 && (
            <div className="joints-container">
                <h4 className="joints-title">Joint Analysis</h4>
                <div className="joints-grid">
                    {/* Left Arm Column */}
                    <div className="joints-column">
                        <span className="column-label">Left Arm</span>
                        {Object.entries(joints)
                        .filter(([_, joint]) => joint.arm === 'left_arm')
                        .map(([key, joint]) => (
                            <div 
                                key={key}
                                className={`joint-card ${joint.is_accurate ? 'joint-good' : 'joint-bad'}`}
                            >
                                <div className="joint-header">
                                    <span className="joint-name">{joint.joint}</span>
                                    <span className={`joint-status ${joint.is_accurate ? 'status-good' : 'status-bad'}`}>
                                        {joint.is_accurate ? '✓' : '✗'}
                                    </span>
                                </div>
                                <div className="joint-deviation">
                                    <div className="deviation-bar">
                                        <div 
                                            className="deviation-fill"
                                            style={{ 
                                                width: `${Math.min(joint.deviation * 100, 100)}%`,
                                                backgroundColor: joint.is_accurate ? '#10b981' : '#ef4444'
                                            }}
                                        />
                                    </div>
                                    <span className="deviation-text">{(joint.deviation * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Right Arm Column */}
                    <div className="joints-column">
                        <span className="column-label">Right Arm</span>
                        {Object.entries(joints)
                        .filter(([_, joint]) => joint.arm === 'right_arm')
                        .map(([key, joint]) => (
                            <div 
                                key={key}
                                className={`joint-card ${joint.is_accurate ? 'joint-good' : 'joint-bad'}`}
                            >
                                <div className="joint-header">
                                    <span className="joint-name">{joint.joint}</span>
                                    <span className={`joint-status ${joint.is_accurate ? 'status-good' : 'status-bad'}`}>
                                        {joint.is_accurate ? '✓' : '✗'}
                                    </span>
                                </div>
                                <div className="joint-deviation">
                                    <div className="deviation-bar">
                                        <div 
                                            className="deviation-fill"
                                            style={{ 
                                                width: `${Math.min(joint.deviation * 100, 100)}%`,
                                                backgroundColor: joint.is_accurate ? '#10b981' : '#ef4444'
                                            }}
                                        />
                                    </div>
                                    <span className="deviation-text">{(joint.deviation * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            )}
            
            {/* Error Display */}
            {error && (
                <div className="error-display">
                    <span className="error-icon">⚠️</span>
                    <span className="error-text">{error}</span>
                </div>
            )}

            {/* Empty State */}
            {score === null && Object.keys(joints).length === 0 && !error && (
                <div className="empty-state">
                    <span className="empty-icon">📷</span>
                    <span className="empty-text">Start the camera to begin posture analysis</span>
                </div>
            )}
        </div>
    );
}
