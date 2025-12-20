import { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import './LogViewer.css';

export default function LogViewer({ onClose }) {
    const [logs, setLogs] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const logEndRef = useRef(null);

    const fetchLogs = async () => {
        try {
            setIsLoading(true);
            const data = await api.fetchLogs(200);
            setLogs(data.logs || []);
            setError(null);
        } catch (err) {
            setError('Failed to load logs');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();

        // Auto-refresh every 5 seconds
        const interval = setInterval(fetchLogs, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        // Scroll to bottom on new logs
        if (logEndRef.current) {
            logEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    return (
        <div className="log-viewer-overlay">
            <div className="log-viewer-modal">
                <div className="log-viewer-header">
                    <h2>Server Logs & Resources</h2>
                    <div className="log-actions">
                        <button className="refresh-btn" onClick={fetchLogs} disabled={isLoading}>
                            Refresh
                        </button>
                        <button className="close-btn" onClick={onClose}>
                            Close
                        </button>
                    </div>
                </div>

                <div className="log-content">
                    {isLoading && logs.length === 0 ? (
                        <div className="loading">Loading logs...</div>
                    ) : error ? (
                        <div className="error">{error}</div>
                    ) : (
                        <>
                            {logs.map((log, index) => {
                                // Highlight based on log level
                                let className = 'log-line';
                                if (log.includes(' ERROR ')) className += ' log-error';
                                if (log.includes('Usage:')) className += ' log-usage';

                                return (
                                    <div key={index} className={className}>
                                        {log}
                                    </div>
                                );
                            })}
                            <div ref={logEndRef} />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
