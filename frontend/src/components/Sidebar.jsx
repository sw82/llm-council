import { useState, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onRenameConversation,
  onDeleteConversation,
  onShowLogs,
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const startEditing = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title || 'New Conversation');
  };

  const handleCreateConversation = (e) => {
    // Stop editing if we are editing
    if (editingId) {
      setEditingId(null);
    }
    onNewConversation();
  }

  const saveTitle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (editingId && editTitle.trim()) {
      onRenameConversation(editingId, editTitle.trim());
      setEditingId(null);
    }
  };

  const cancelEditing = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(id);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={handleCreateConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === currentConversationId ? 'active' : ''
                }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              {editingId === conv.id ? (
                <form className="edit-form" onSubmit={saveTitle} onClick={(e) => e.stopPropagation()}>
                  <input
                    className="edit-input"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={saveTitle}
                    autoFocus
                  />
                </form>
              ) : (
                <>
                  <div className="conversation-info">
                    <div className="conversation-title">
                      {conv.title || 'New Conversation'}
                    </div>
                    <div className="conversation-meta">
                      <span>{conv.message_count} messages</span>
                      {(conv.total_cost !== undefined && conv.total_cost >= 0) && (
                        <span className="conversation-cost">
                          ${conv.total_cost.toFixed(4)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="conversation-actions">
                    <button
                      className="action-btn"
                      onClick={(e) => startEditing(e, conv)}
                      title="Rename"
                    >
                      ✎
                    </button>
                    <button
                      className="action-btn"
                      onClick={(e) => handleDelete(e, conv.id)}
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <button className="logs-btn" onClick={onShowLogs}>
          📊 View Logs & Resources
        </button>
      </div>
    </div>
  );
}
