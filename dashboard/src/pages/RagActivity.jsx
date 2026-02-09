import { useEffect, useState } from 'react';
import { getRagActivity } from '../api';
import { Database, Download, Upload, Search } from 'lucide-react';

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

export default function RagActivity() {
    const [activity, setActivity] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const res = await getRagActivity(100);
                setActivity(res.data);
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
            <h1 className="text-2xl font-bold lg:ml-0 ml-12">RAG Activity</h1>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}>
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
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(0, 210, 106, 0.2)' }}>
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
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)' }}>
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
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)' }}>
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
                        activity.map((item) => {
                            const Icon = ACTION_ICONS[item.action] || Database;
                            const color = ACTION_COLORS[item.action] || 'var(--text-secondary)';

                            return (
                                <div key={item.id} className="flex items-start gap-4 p-3 rounded-lg bg-[var(--bg-tertiary)]">
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
                                        </div>
                                        {item.query && (
                                            <p className="text-sm text-[var(--text-secondary)] truncate">
                                                Query: {item.query}
                                            </p>
                                        )}
                                        <div className="flex gap-4 mt-1 text-sm text-[var(--text-secondary)]">
                                            {item.tweet_count > 0 && (
                                                <span>{item.tweet_count} tweets</span>
                                            )}
                                            {item.results_count > 0 && (
                                                <span>{item.results_count} results</span>
                                            )}
                                        </div>
                                    </div>
                                    <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap">
                                        {new Date(item.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
}
