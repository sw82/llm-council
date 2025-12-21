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
            loadData();
        }
    }, [isOpen]);

    const loadData = async () => {
        try {
            setIsLoading(true);
            const [modelsData, configData] = await Promise.all([
                api.fetchModels(),
                api.fetchConfig()
            ]);

            let models = modelsData.models || [];

            // Define popular models keywords/ids to prioritize
            const priorityTerms = [
                'gpt-4', 'claude-3', 'gemini', 'llama-3'
            ];

            models.sort((a, b) => {
                const aName = a.name.toLowerCase();
                const bName = b.name.toLowerCase();
                const aId = a.id.toLowerCase();
                const bId = b.id.toLowerCase();

                const aPriority = priorityTerms.findIndex(term => aName.includes(term) || aId.includes(term));
                const bPriority = priorityTerms.findIndex(term => bName.includes(term) || bId.includes(term));

                // If both are priority models, sort by which priority term comes first in the list
                if (aPriority !== -1 && bPriority !== -1) {
                    if (aPriority !== bPriority) return aPriority - bPriority;
                    return aName.localeCompare(bName);
                }

                // If only a is priority, it comes first
                if (aPriority !== -1) return -1;
                // If only b is priority, it comes first
                if (bPriority !== -1) return 1;

                // Otherwise sort alphabetically
                return aName.localeCompare(bName);
            });

            setAvailableModels(models);

            // Apply defaults if no initial settings provided
            if (!initialSettings.council_models || initialSettings.council_models.length === 0) {
                if (configData.council_models) {
                    setSelectedCouncil(configData.council_models);
                }
            }

            if (!initialSettings.chairman_model) {
                if (configData.chairman_model) {
                    setSelectedChairman(configData.chairman_model);
                }
            }

            setError(null);
        } catch (err) {
            setError('Failed to load models or configuration');
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
                                                <div>In: ${parseFloat(m.pricing?.prompt || 0) * 1000000} / 1M</div>
                                                <div>Out: ${parseFloat(m.pricing?.completion || 0) * 1000000} / 1M</div>
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
