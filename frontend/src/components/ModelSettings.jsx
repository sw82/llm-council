import { useState, useEffect } from 'react';
import { api } from '../api';
import './ModelSettings.css';

export default function ModelSettings({ isOpen, onClose, onSave, initialSettings }) {
    const [availableModels, setAvailableModels] = useState([]);
    const [selectedCouncil, setSelectedCouncil] = useState(initialSettings.council_models || []);
    const [selectedChairman, setSelectedChairman] = useState(initialSettings.chairman_model || '');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen) {
            fetchModels();
        }
    }, [isOpen]);

    const fetchModels = async () => {
        try {
            setIsLoading(true);
            const data = await api.fetchModels();
            setAvailableModels(data.models || []);
            setError(null);
        } catch (err) {
            setError('Failed to load models');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleCouncilModel = (modelId) => {
        setSelectedCouncil(prev => {
            if (prev.includes(modelId)) {
                return prev.filter(id => id !== modelId);
            } else {
                return [...prev, modelId];
            }
        });
    };

    const handleSave = () => {
        onSave({
            council_models: selectedCouncil.length > 0 ? selectedCouncil : null,
            chairman_model: selectedChairman || null
        });
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="model-settings-overlay">
            <div className="model-settings-modal">
                <div className="settings-header">
                    <h2>Council Configuration</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="settings-content">
                    {isLoading ? (
                        <div className="loading">Loading models...</div>
                    ) : error ? (
                        <div className="error">{error}</div>
                    ) : (
                        <>
                            <div className="setting-section">
                                <h3>Chairman Model</h3>
                                <p className="description">Select the model that synthesizes the final answer.</p>
                                <select
                                    value={selectedChairman}
                                    onChange={(e) => setSelectedChairman(e.target.value)}
                                    className="model-select"
                                >
                                    <option value="">Default (Configured)</option>
                                    {availableModels.map(m => (
                                        <option key={m.id} value={m.id}>
                                            {m.name} ({m.id})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-section">
                                <h3>Council Members</h3>
                                <p className="description">Select models that provide initial responses and verify each other.</p>
                                <div className="models-grid">
                                    {availableModels.map(m => (
                                        <div
                                            key={m.id}
                                            className={`model-option ${selectedCouncil.includes(m.id) ? 'selected' : ''}`}
                                            onClick={() => toggleCouncilModel(m.id)}
                                        >
                                            <div className="model-name">{m.name}</div>
                                            <div className="model-id">{m.id}</div>
                                            <div className="model-pricing">
                                                Input: ${parseFloat(m.pricing?.prompt || 0) * 1000000} / 1M
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                <div className="settings-footer">
                    <button className="cancel-btn" onClick={onClose}>Cancel</button>
                    <button className="save-btn" onClick={handleSave}>Apply Configuration</button>
                </div>
            </div>
        </div>
    );
}
