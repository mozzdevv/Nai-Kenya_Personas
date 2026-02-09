import { useEffect, useState } from 'react';
import { getPosts } from '../api';
import { MessageSquare, Heart, Repeat2, MessageCircle, Filter } from 'lucide-react';

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
        : posts.filter(p => p.persona.toLowerCase() === filter);

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
                                <th>Type</th>
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
                                    <tr key={post.id}>
                                        <td>
                                            <span className={`font-medium ${post.persona === 'Kamau' ? 'persona-kamau' : 'persona-wanjiku'}`}>
                                                {post.persona}
                                            </span>
                                        </td>
                                        <td className="max-w-md">
                                            <p className="truncate">{post.content}</p>
                                        </td>
                                        <td>
                                            <span className="badge badge-success">{post.post_type}</span>
                                        </td>
                                        <td>
                                            <span className={`badge ${post.llm_used === 'grok' ? 'badge-grok' : 'badge-claude'}`}>
                                                {post.llm_used}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="flex gap-3 text-sm text-[var(--text-secondary)]">
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
                                        </td>
                                        <td className="text-sm text-[var(--text-secondary)]">
                                            {new Date(post.created_at).toLocaleString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
