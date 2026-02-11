import { useEffect, useState } from 'react';
import { getValidationConfig } from '../api';
import { ShieldCheck, Target, Languages, AlertCircle, Info, Hash } from 'lucide-react';

export default function Validation() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const res = await getValidationConfig();
                setConfig(res.data);
            } catch (error) {
                console.error('Failed to fetch validation config:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchConfig();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (!config) return <div className="text-center py-12">Failed to load validation config.</div>;

    return (
        <div className="space-y-8 pb-12">
            <header className="lg:ml-0 ml-12">
                <h1 className="text-3xl font-bold">Content Validation Engine</h1>
                <p className="mt-2 text-lg text-[var(--text-secondary)]">
                    Providing transparency into how generated posts are scored for Nairobi authenticity.
                </p>
            </header>

            {/* Core Logic Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {config.scoring_rules.map((rule, i) => (
                    <div key={i} className="card border-t-4" style={{ borderTopColor: i === 0 ? 'var(--accent-orange)' : i === 1 ? 'var(--accent-green)' : 'var(--accent-purple)' }}>
                        <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                            {i === 0 ? <AlertCircle size={20} className="text-[var(--accent-orange)]" /> : i === 1 ? <Target size={20} className="text-[var(--accent-green)]" /> : <ShieldCheck size={20} className="text-[var(--accent-purple)]" />}
                            {rule.name}
                        </h3>
                        <div className="text-xs font-mono uppercase text-[var(--text-secondary)] mb-3">{rule.weight}</div>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                            {rule.descr}
                        </p>
                    </div>
                ))}
            </div>

            {/* Detailed Patterns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Patterns & Markers */}
                <div className="space-y-6">
                    <div className="card h-full">
                        <div className="card-header mb-4">
                            <Languages size={20} />
                            <span>Linguistic Markers</span>
                        </div>
                        <div className="space-y-6">
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-[var(--accent-green)] mb-3">Swahili/Sheng (High Density Required)</h4>
                                <div className="flex flex-wrap gap-1.5">
                                    {config.language_markers.swahili_sheng.map(word => (
                                        <span key={word} className="px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs border border-[var(--bg-secondary)]">{word}</span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-[var(--accent-purple)] mb-3">Kikuyu (Authenticity Boost)</h4>
                                <div className="flex flex-wrap gap-1.5">
                                    {config.language_markers.kikuyu.map(word => (
                                        <span key={word} className="px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs border border-[var(--bg-secondary)]">{word}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Anti-Patterns Siderbar */}
                <div className="space-y-6">
                    <div className="card border-l-4 border-[var(--accent-orange)]">
                        <div className="card-header mb-4">
                            <AlertCircle size={20} className="text-[var(--accent-orange)]" />
                            <span>AI Red Flags (Auto-Fail or Heavy Deductions)</span>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <p className="text-xs font-bold uppercase text-[var(--text-secondary)] mb-2">English Proverb Framers</p>
                                <div className="space-y-1">
                                    {config.ai_patterns.map(p => (
                                        <div key={p} className="text-sm text-[var(--text-primary)] pl-3 border-l border-[var(--bg-tertiary)] italic">"{p}"</div>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <p className="text-xs font-bold uppercase text-[var(--text-secondary)] mb-2">Robotic Formal Connectors</p>
                                <div className="flex flex-wrap gap-2">
                                    {config.formal_connectors.slice(0, 10).map(c => (
                                        <span key={c} className="text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded">{c}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header mb-4">
                            <Hash size={20} className="text-[var(--accent-green)]" />
                            <span>Approved Local Hashtags</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {config.approved_hashtags.map(tag => (
                                <span key={tag} className="text-xs font-mono text-[var(--accent-green)] bg-[var(--accent-green)]/10 px-2 py-1 rounded">{tag}</span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Contextual Infographic-style Explanation */}
            <div className="card bg-[var(--bg-tertiary)] border-none">
                <div className="flex items-start gap-4">
                    <Info size={24} className="text-[var(--accent-green)] mt-1 shrink-0" />
                    <div>
                        <h3 className="text-lg font-bold mb-2">Real-time Grounding</h3>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                            The validator doesn't just check keywords; it checks the **Nairobi pulse**. If a persona posts about "asubuhi" (morning) when it's 10 PM in Nairobi, the validator flags a contextual mismatch. It also monitors word length and punctuation density—real Nairobi tweets are fragmented, informal, and rarely use perfect grammar or excessive punctuation.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
