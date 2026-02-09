import { useEffect, useState } from 'react';
import { getRoutingStats, getRoutingHistory } from '../api';
import { GitBranch, Zap, Sparkles } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = {
    grok: '#f59e0b',
    claude: '#8b5cf6',
};

export default function Routing() {
    const [stats, setStats] = useState({});
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, historyRes] = await Promise.all([
                    getRoutingStats(),
                    getRoutingHistory(50),
                ]);
                setStats(statsRes.data);
                setHistory(historyRes.data);
            } catch (error) {
                console.error('Failed to fetch routing data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const pieData = Object.entries(stats).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
    }));

    const total = pieData.reduce((sum, item) => sum + item.value, 0);

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold lg:ml-0 ml-12">LLM Routing</h1>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(0, 210, 106, 0.2)' }}>
                            <GitBranch size={20} style={{ color: 'var(--accent-green)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Total Decisions</p>
                            <p className="text-2xl font-bold">{total}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)' }}>
                            <Zap size={20} style={{ color: 'var(--accent-orange)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Grok Usage</p>
                            <p className="text-2xl font-bold">{stats.grok || 0}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)' }}>
                            <Sparkles size={20} style={{ color: 'var(--accent-purple)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Claude Usage</p>
                            <p className="text-2xl font-bold">{stats.claude || 0}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pie Chart */}
                <div className="card">
                    <div className="card-header">
                        <GitBranch size={20} />
                        <span>Distribution</span>
                    </div>
                    {pieData.length === 0 ? (
                        <p className="text-[var(--text-secondary)] text-center py-8">No data yet</p>
                    ) : (
                        <>
                            <ResponsiveContainer width="100%" height={250}>
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase()] || '#888'} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--bg-secondary)',
                                            border: '1px solid var(--bg-tertiary)',
                                            borderRadius: '8px'
                                        }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </>
                    )}
                </div>

                {/* Recent Decisions */}
                <div className="card">
                    <div className="card-header">
                        <GitBranch size={20} />
                        <span>Recent Decisions</span>
                    </div>
                    <div className="space-y-3 max-h-[300px] overflow-auto">
                        {history.length === 0 ? (
                            <p className="text-[var(--text-secondary)] text-center py-8">No decisions yet</p>
                        ) : (
                            history.slice(0, 15).map((item) => (
                                <div key={item.id} className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className={`badge ${item.decision === 'grok' ? 'badge-grok' : 'badge-claude'}`}>
                                            {item.decision}
                                        </span>
                                        <span className="text-xs text-[var(--text-secondary)]">
                                            {new Date(item.created_at).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <p className="text-sm truncate">{item.topic}</p>
                                    <div className="flex gap-2 mt-1 text-xs text-[var(--text-secondary)]">
                                        <span>Task: {item.task}</span>
                                        <span>•</span>
                                        <span>Score: {item.trigger_score}</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
