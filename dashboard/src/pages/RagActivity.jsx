import { useEffect, useState } from 'react';
import { getRagActivity } from '../api';
import { Database, Download, Upload, Search, Info } from 'lucide-react';

const ACTION_ICONS = {
    fetch: Download,
    store: Upload,
    retrieve: Search,
};

const ACTION_COLORS = {
    fetch: 'var(--accent-blue)',
    store: 'var(--accent-green)',
    retrieve: 'var(--accent-purple)',
};

const ACTION_LABELS = {
    fetch: 'Fetched tweets from X seed accounts into the knowledge base',
    store: 'Stored tweet embeddings in Pinecone vector database',
    retrieve: 'Retrieved similar reference tweets for AI-generated content',
};

// Extracted into its own component so useState is called at the top level (Rules of Hooks)
function ActivityItem({ item }) {
    const [expanded, setExpanded] = useState(false);

    const Icon = ACTION_ICONS[item.action] || Database;
    const color = ACTION_COLORS[item.action] || 'var(--text-secondary)';

    // Parse details safely
    let details = [];
    try {
        if (item.details && item.details !== "null") {
            const parsed = JSON.parse(item.details);
            details = Array.isArray(parsed) ? parsed : [];
        }
    } catch (e) {
        details = [];
    }

    return (
        <div className="rounded-lg bg-[var(--bg-tertiary)] overflow-hidden">
            <div
                className="flex items-start gap-4 p-3 cursor-pointer hover:bg-[var(--bg-secondary)] transition-colors"
                onClick={() => details.length > 0 && setExpanded(!expanded)}
            >
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}20` }}>
                    <Icon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium capitalize">{item.action}</span>
                        {item.source && (
                            <span className="text-sm text-[var(--text-secondary)]">
                                from @{item.source}
                            </span>
                        )}
                        {item.persona && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] text-[var(--text-primary)] font-medium border border-[var(--bg-tertiary)]">
                                {item.persona}
                            </span>
                        )}
                    </div>
                    {item.query && (
                        <p className="text-sm text-[var(--text-secondary)] truncate">
                            Topic: <span className="font-medium text-[var(--text-primary)]">{item.query}</span>
                        </p>
                    )}
                    {/* Inline explanation */}
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5 italic">
                        {ACTION_LABELS[item.action] || 'RAG pipeline activity'}
                    </p>
                    <div className="flex gap-4 mt-1 text-sm text-[var(--text-secondary)]">
                        {item.tweet_count > 0 && (
                            <span>{item.tweet_count} tweets</span>
                        )}
                        {item.results_count > 0 && (
                            <span className="flex items-center gap-1">
                                {item.results_count} reference tweets found
                                {details.length > 0 && (
                                    <span className="text-xs bg-[var(--bg-secondary)] px-1.5 rounded cursor-pointer">
                                        {expanded ? '▲ Collapse' : '▼ View Matches'}
                                    </span>
                                )}
                            </span>
                        )}
                    </div>
                </div>
                <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap">
                    {new Date(item.created_at).toLocaleTimeString()}
                </span>
            </div>

            {/* Expanded Details View */}
            {expanded && details.length > 0 && (
                <div className="px-4 pb-4 pt-0 space-y-2 border-t border-[var(--bg-secondary)] bg-[var(--bg-tertiary)]">
                    <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase mt-3 mb-1">
                        Retrieved Reference Tweets
                    </p>
                    <p className="text-xs text-[var(--text-secondary)] mb-2">
                        These real tweets were fed to the AI as style references for generating authentic content.
                    </p>
                    {details.map((detail, idx) => (
                        <div key={idx} className="bg-[var(--bg-primary)] p-3 rounded border border-[var(--bg-secondary)]">
                            <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-mono text-[var(--text-secondary)]">@{detail.source || 'unknown'}</span>
                                <span
                                    className="text-xs font-bold px-1.5 py-0.5 rounded"
                                    style={{
                                        backgroundColor: (detail.score || 0) >= 0.5 ? '#dcfce7' : '#fef9c3',
                                        color: (detail.score || 0) >= 0.5 ? '#166534' : '#854d0e',
                                    }}
                                    title="Cosine similarity — how semantically close this tweet is to the query topic (100% = identical meaning)"
                                >
                                    {((detail.score || 0) * 100).toFixed(1)}% Similar
                                </span>
                            </div>
                            <p className="text-sm text-[var(--text-primary)] font-serif italic">
                                "{detail.text}"
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default function RagActivity() {
    const [activity, setActivity] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const res = await getRagActivity(100);
                setActivity(Array.isArray(res.data) ? res.data : []);
            } catch (error) {
                console.error('Failed to fetch RAG activity:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchActivity();
        const interval = setInterval(fetchActivity, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    // Calculate stats
    const stats = {
        fetch: activity.filter(a => a.action === 'fetch').length,
        store: activity.filter(a => a.action === 'store').length,
        retrieve: activity.filter(a => a.action === 'retrieve').length,
        totalTweets: activity.filter(a => a.action === 'store').reduce((sum, a) => sum + (a.tweet_count || 0), 0),
    };

    return (
        <div className="space-y-6">
            <header className="lg:ml-0 ml-12">
                <h1 className="text-2xl font-bold">RAG Activity</h1>
                <p className="text-[var(--text-secondary)]">
                    Retrieval-Augmented Generation — the system finds real Kikuyu/Kenyan tweets to guide AI content creation.
                </p>
            </header>

            {/* How it works explainer */}
            <div className="card border-l-4" style={{ borderLeftColor: 'var(--accent-green)' }}>
                <div className="flex items-start gap-3">
                    <Info size={18} className="mt-0.5 shrink-0" style={{ color: 'var(--accent-green)' }} />
                    <div className="text-sm text-[var(--text-secondary)]">
                        <p className="font-semibold text-[var(--text-primary)] mb-1">How RAG Works</p>
                        <p>Before generating each post, the bot searches the Pinecone vector database for real tweets that semantically match the current topic. These reference tweets are fed to the AI as style examples, helping it produce culturally authentic content. The <strong>similarity score</strong> (0–100%) measures how closely each reference tweet relates to the query topic.</p>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            <Download size={20} style={{ color: 'var(--accent-blue)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Fetches</p>
                            <p className="text-2xl font-bold">{stats.fetch}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            <Upload size={20} style={{ color: 'var(--accent-green)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Stores</p>
                            <p className="text-2xl font-bold">{stats.store}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            <Search size={20} style={{ color: 'var(--accent-purple)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Retrievals</p>
                            <p className="text-2xl font-bold">{stats.retrieve}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            <Database size={20} style={{ color: 'var(--accent-orange)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Tweets Stored</p>
                            <p className="text-2xl font-bold">{stats.totalTweets}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Activity Log */}
            <div className="card">
                <div className="card-header">
                    <Database size={20} />
                    <span>Activity Log</span>
                </div>
                <div className="space-y-3 max-h-[500px] overflow-auto">
                    {activity.length === 0 ? (
                        <p className="text-[var(--text-secondary)] text-center py-8">No activity yet</p>
                    ) : (
                        activity.map((item) => (
                            <ActivityItem key={item.id} item={item} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
