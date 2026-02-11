import { useEffect, useState } from 'react';
import { getPosts } from '../api';
import { MessageSquare, Heart, Repeat2, MessageCircle, Filter, Info, ShieldCheck, ShieldAlert, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

function PostRow({ post }) {
    const [expanded, setExpanded] = useState(false);
    const score = post.authenticity_score ?? 100;
    const issues = post.validation_issues ? JSON.parse(post.validation_issues) : [];
    const warnings = post.validation_warnings ? JSON.parse(post.validation_warnings) : [];

    return (
        <>
            <tr
                className={`cursor-pointer hover:bg-[var(--bg-secondary)] transition-colors ${expanded ? 'bg-[var(--bg-secondary)]' : ''}`}
                onClick={() => setExpanded(!expanded)}
            >
                <td>
                    <span className={`font-medium ${post.persona.toLowerCase().includes('kamau') ? 'persona-kamau' : 'persona-wanjiku'}`}>
                        {post.persona}
                    </span>
                </td>
                <td className="max-w-xs xl:max-w-md">
                    <p className={expanded ? '' : 'truncate'}>{post.content}</p>
                </td>
                <td>
                    <div className="flex items-center gap-2">
                        <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${score >= 80 ? 'bg-green-400/10 text-green-400' :
                                score >= 50 ? 'bg-yellow-400/10 text-yellow-400' :
                                    'bg-red-400/10 text-red-400'
                                }`}
                        >
                            {score >= 80 ? <ShieldCheck size={12} /> : <ShieldAlert size={12} />}
                            {score}%
                        </span>
                        {expanded ? <ChevronUp size={14} className="text-[var(--text-secondary)]" /> : <ChevronDown size={14} className="text-[var(--text-secondary)]" />}
                    </div>
                </td>
                <td>
                    <span className={`badge ${post.llm_used === 'grok' ? 'badge-grok' : 'badge-claude'}`}>
                        {post.llm_used}
                    </span>
                </td>
                <td>
                    <div className="flex gap-3 text-sm text-[var(--text-secondary)]">
                        <span className="flex items-center gap-1"><Heart size={14} /> {post.likes || 0}</span>
                        <span className="flex items-center gap-1"><Repeat2 size={14} /> {post.retweets || 0}</span>
                    </div>
                </td>
                <td className="text-xs text-[var(--text-secondary)]">
                    {new Date(post.created_at.replace(' ', 'T')).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </td>
            </tr>
            {expanded && (
                <tr className="bg-[var(--bg-secondary)] text-sm">
                    <td colSpan={6} className="px-6 py-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2">Original Generation</h4>
                                <p className="text-[var(--text-primary)] leading-relaxed bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--bg-tertiary)]">
                                    {post.content}
                                </p>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2">Validation Analysis</h4>
                                    {issues.length === 0 && warnings.length === 0 ? (
                                        <div className="flex items-center gap-2 text-green-400">
                                            <ShieldCheck size={16} />
                                            <span>Perfect match for persona and context.</span>
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {issues.map((issue, i) => (
                                                <div key={i} className="flex items-start gap-2 text-red-400">
                                                    <AlertCircle size={14} className="mt-0.5 shrink-0" />
                                                    <span>{issue}</span>
                                                </div>
                                            ))}
                                            {warnings.map((warning, i) => (
                                                <div key={i} className="flex items-start gap-2 text-yellow-400">
                                                    <Info size={14} className="mt-0.5 shrink-0" />
                                                    <span>{warning}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                <div className="text-xs text-[var(--text-secondary)]">
                                    Type: <span className="font-mono text-[var(--text-primary)]">{post.post_type}</span> •
                                    ID: <span className="font-mono text-[var(--text-primary)]">{post.id}</span>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
}

export default function Posts() {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                const res = await getPosts(100);
                setPosts(res.data);
            } catch (error) {
                console.error('Failed to fetch posts:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchPosts();
        const interval = setInterval(fetchPosts, 30000);
        return () => clearInterval(interval);
    }, []);

    const filteredPosts = filter === 'all'
        ? posts
        : posts.filter(p => p.persona.toLowerCase().includes(filter));

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4 lg:ml-0 ml-12">
                <h1 className="text-2xl font-bold">Posts</h1>

                {/* Filter */}
                <div className="flex items-center gap-2">
                    <Filter size={18} className="text-[var(--text-secondary)]" />
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="input w-40"
                    >
                        <option value="all">All Personas</option>
                        <option value="kamau">Kamau</option>
                        <option value="wanjiku">Wanjiku</option>
                    </select>
                </div>
            </div>

            {/* Posts Table */}
            <div className="card">
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Persona</th>
                                <th>Content</th>
                                <th>Authenticity</th>
                                <th>LLM</th>
                                <th>Engagement</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredPosts.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-8 text-[var(--text-secondary)]">
                                        No posts found
                                    </td>
                                </tr>
                            ) : (
                                filteredPosts.map((post) => (
                                    <PostRow key={post.id} post={post} />
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
