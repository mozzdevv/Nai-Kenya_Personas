import { useEffect, useState } from 'react';
import { getStats, getPosts, getRoutingStats } from '../api';
import {
    TrendingUp,
    MessageSquare,
    Heart,
    Repeat2,
    MessageCircle,
    Brain
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = {
    grok: '#374151',    // dark gray
    claude: '#9ca3af',  // light gray
    kamau: '#1f2937',   // very dark gray
    wanjiku: '#6b7280', // medium gray
};

function StatCard({ icon: Icon, label, value, color }) {
    return (
        <div className="card">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-[var(--text-secondary)] text-sm">{label}</p>
                    <p className="text-3xl font-bold mt-1">{value}</p>
                </div>
                <div className={`p-3 rounded-xl bg-opacity-20`} style={{ backgroundColor: `${color}20` }}>
                    <Icon size={24} style={{ color }} />
                </div>
            </div>
        </div>
    );
}

function RecentPosts({ posts }) {
    return (
        <div className="card">
            <div className="card-header">
                <MessageSquare size={20} />
                <span>Recent Posts</span>
            </div>
            <div className="space-y-4 max-h-96 overflow-auto">
                {posts.length === 0 ? (
                    <p className="text-[var(--text-secondary)] text-center py-8">No posts yet</p>
                ) : (
                    posts.slice(0, 10).map((post) => (
                        <div key={post.id} className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                            <div className="flex items-center gap-2 mb-2">
                                <span className={`font-medium ${post.persona.toLowerCase().includes('kamau') ? 'persona-kamau' : 'persona-wanjiku'}`}>
                                    {post.persona}
                                </span>
                                <span className={`badge ${post.llm_used === 'grok' ? 'badge-grok' : 'badge-claude'}`}>
                                    {post.llm_used}
                                </span>
                                <span className="text-xs text-[var(--text-secondary)] ml-auto">
                                    {new Date(post.created_at).toLocaleTimeString()}
                                </span>
                            </div>
                            <p className="text-sm">{post.content}</p>
                            <div className="flex gap-4 mt-2 text-sm text-[var(--text-secondary)]">
                                <span className="flex items-center gap-1">
                                    <Heart size={14} /> {post.likes || 0}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Repeat2 size={14} /> {post.retweets || 0}
                                </span>
                                <span className="flex items-center gap-1">
                                    <MessageCircle size={14} /> {post.replies || 0}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

function LLMPieChart({ data }) {
    const chartData = Object.entries(data || {}).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
    }));

    return (
        <div className="card">
            <div className="card-header">
                <Brain size={20} />
                <span>LLM Usage</span>
            </div>
            {chartData.length === 0 ? (
                <p className="text-[var(--text-secondary)] text-center py-8">No data yet</p>
            ) : (
                <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={COLORS[entry.name.toLowerCase()] || '#888'}
                                />
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
            )}
            <div className="flex justify-center gap-6 mt-4">
                {chartData.map((item) => (
                    <div key={item.name} className="flex items-center gap-2">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: COLORS[item.name.toLowerCase()] }}
                        />
                        <span className="text-sm">{item.name}: {item.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function Overview() {
    const [stats, setStats] = useState(null);
    const [posts, setPosts] = useState([]);
    const [routingStats, setRoutingStats] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, postsRes, routingRes] = await Promise.all([
                    getStats(),
                    getPosts(10),
                    getRoutingStats(),
                ]);
                setStats(statsRes.data);
                setPosts(postsRes.data);
                setRoutingStats(routingRes.data);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const totalPosts = Object.values(stats?.by_persona || {}).reduce((a, b) => a + b, 0);
    const engagement = stats?.engagement || {};

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold lg:ml-0 ml-12">Overview</h1>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={MessageSquare}
                    label="Total Posts"
                    value={totalPosts}
                    color="var(--accent-green)"
                />
                <StatCard
                    icon={Heart}
                    label="Total Likes"
                    value={engagement.likes || 0}
                    color="var(--accent-red)"
                />
                <StatCard
                    icon={Repeat2}
                    label="Total Retweets"
                    value={engagement.retweets || 0}
                    color="var(--accent-blue)"
                />
                <StatCard
                    icon={MessageCircle}
                    label="Total Replies"
                    value={engagement.replies || 0}
                    color="var(--accent-purple)"
                />
            </div>

            {/* Charts & Posts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RecentPosts posts={posts} />
                <LLMPieChart data={routingStats} />
            </div>
        </div>
    );
}
