import React, { useState, useEffect } from 'react';
import api from '../api';
import { User, MessageSquare, BookOpen, Settings, Fingerprint } from 'lucide-react';

const PersonaCard = ({ persona, color }) => {
    const [showPrompt, setShowPrompt] = useState(false);

    // Helper to generate a prompt from persona object (since backend returns object now)
    const systemPrompt = `You are ${persona.name} (${persona.handle})...
PERSONALITY: ${persona.personality_traits.join(", ")}
TONE: ${persona.tone}
TOPICS: ${persona.topics.join(", ")}
PROVERB STYLE: ${persona.proverb_style}
PHRASES:
${persona.signature_phrases.map(p => `  - ${p}`).join("\n")}`;

    return (
        <div className="card h-full flex flex-col">
            <div className="flex items-center gap-4 border-b border-[var(--bg-tertiary)] pb-4 mb-4">
                <div className="p-3 rounded-xl bg-[var(--bg-tertiary)]">
                    <User size={24} style={{ color }} />
                </div>
                <div>
                    <h2 className="text-xl font-bold">{persona.name}</h2>
                    <p className="text-sm text-[var(--text-secondary)] font-mono">{persona.handle}</p>
                </div>
            </div>

            <div className="space-y-6 flex-grow">
                {/* Description & Tone */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                        <Fingerprint size={14} /> Identity
                    </div>
                    <p className="text-sm leading-relaxed mb-3">
                        {persona.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                        <span className="badge" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                            Tone: {persona.tone}
                        </span>
                        {persona.personality_traits.map(trait => (
                            <span key={trait} className="badge" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                                {trait}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Signature Phrases */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                        <MessageSquare size={14} /> Signature Phrases
                    </div>
                    <ul className="space-y-2">
                        {persona.signature_phrases.map((phrase, i) => (
                            <li key={i} className="text-sm flex items-start gap-2">
                                <span className="text-[var(--text-secondary)] mt-1">•</span>
                                <span className="italic">"{phrase}"</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Proverb Style */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                        <BookOpen size={14} /> Proverb Style
                    </div>
                    <p className="text-sm p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--bg-tertiary)]">
                        {persona.proverb_style}
                    </p>
                </div>
            </div>

            {/* System Prompt Toggle */}
            <div className="mt-6 pt-4 border-t border-[var(--bg-tertiary)]">
                <button
                    onClick={() => setShowPrompt(!showPrompt)}
                    className="text-xs font-medium hover:text-[var(--text-primary)] text-[var(--text-secondary)] flex items-center gap-1 transition-colors"
                >
                    {showPrompt ? 'Hide System Prompt' : 'View Raw System Prompt'}
                </button>

                {showPrompt && (
                    <div className="mt-3 bg-black rounded-lg p-4 overflow-x-auto">
                        <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                            {systemPrompt}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
};

const BotLogic = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const resp = await api.get('/logic');
                setData(resp.data);
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch bot logic:', error);
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return (
        <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-4 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!data) return <div className="text-center py-12 text-[var(--text-secondary)]">Failed to load bot logic.</div>;

    return (
        <div className="space-y-8 pb-12">
            <header className="lg:ml-0 ml-12">
                <h1 className="text-3xl font-bold tracking-tight">Bot Logic & Brain</h1>
                <p className="mt-2 text-lg text-[var(--text-secondary)]">
                    Deep dive into persona identities, system prompts, and configuration.
                </p>
            </header>

            {/* Persona Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PersonaCard persona={data.kamau} color="var(--accent-orange)" />
                <PersonaCard persona={data.wanjiku} color="var(--accent-purple)" />
            </div>

            {/* Configuration */}
            <div className="card">
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                    <Settings className="text-[var(--text-secondary)]" /> System Configuration
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="p-4 rounded-lg bg-[var(--bg-tertiary)]">
                        <dt className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Loop Interval</dt>
                        <dd className="mt-1 text-2xl font-bold">{data.config.loop_interval_hours}h</dd>
                    </div>
                    <div className="p-4 rounded-lg bg-[var(--bg-tertiary)]">
                        <dt className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Mode</dt>
                        <dd className="mt-1 text-2xl font-bold">
                            {data.config.dry_run ? 'Dry Run' : 'Live'}
                        </dd>
                    </div>
                    <div className="p-4 rounded-lg bg-[var(--bg-tertiary)]">
                        <dt className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Grok Model</dt>
                        <dd className="mt-1 text-sm font-bold truncate" title={data.config.grok_model}>
                            {data.config.grok_model}
                        </dd>
                    </div>
                    <div className="p-4 rounded-lg bg-[var(--bg-tertiary)]">
                        <dt className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Claude Model</dt>
                        <dd className="mt-1 text-sm font-bold truncate" title={data.config.claude_model}>
                            {data.config.claude_model}
                        </dd>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BotLogic;
