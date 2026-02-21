import { useEffect, useState } from 'react';
import api, { getRoutingStats, getRoutingHistory } from '../api';
import { formatDualTime } from '../utils';
import { GitBranch, Zap, Sparkles, AlertCircle, BookOpen, Info } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = {
    grok: 'var(--accent-orange)',
    claude: 'var(--accent-purple)',
};

// Extracted into its own component to avoid Rules of Hooks violation
function DecisionRow({ item }) {
    const [showReason, setShowReason] = useState(false);

    // Parse triggers safely
    let triggers = [];
    try {
        triggers = typeof item.triggers_matched === 'string'
            ? JSON.parse(item.triggers_matched)
            : item.triggers_matched || [];
    } catch (e) { triggers = []; }

    const score = item.trigger_score || 0;
    const isGrok = item.decision === 'grok';

    return (
        <>
            <tr
                className="border-b border-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] cursor-pointer"
                onClick={() => setShowReason(!showReason)}
            >
                <td className="px-4 py-3 whitespace-nowrap text-[var(--text-secondary)] text-xs">
                    {formatDualTime(item.created_at)}
                </td>
                <td className="px-4 py-3 font-medium text-[var(--text-primary)]">
                    <div>{item.topic}</div>
                    <div className="text-xs text-[var(--text-secondary)] mt-0.5">{item.task}</div>
                </td>
                <td className="px-4 py-3 text-[var(--text-secondary)]">
                    {item.persona}
                </td>
                <td className="px-4 py-3 text-center">
                    <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold"
                        style={{
                            backgroundColor: score >= 2 ? '#f3e8ff' : score === 1 ? '#fef9c3' : '#f1f5f9',
                            color: score >= 2 ? '#7c3aed' : score === 1 ? '#854d0e' : '#64748b',
                        }}
                        title={`${score} Claude trigger keyword(s) found. Score ≥ 2 activates Claude.`}
                    >
                        {score >= 2 ? '🧠' : '⚡'} {score}
                    </span>
                </td>
                <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                        {triggers.length > 0 ? triggers.map((t, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded text-xs border border-[var(--bg-secondary)]">
                                {t}
                            </span>
                        )) : <span className="text-[var(--text-secondary)] text-xs italic">none</span>}
                    </div>
                </td>
                <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${isGrok ? 'bg-amber-100 text-amber-800' : 'bg-purple-100 text-purple-800'}`}>
                        {isGrok ? '⚡ Grok' : '🧠 Claude'}
                    </span>
                </td>
            </tr>
            {/* Expandable reason row */}
            {showReason && item.reason && (
                <tr className="bg-[var(--bg-secondary)] border-b border-[var(--bg-tertiary)]">
                    <td colSpan="6" className="px-4 py-2">
                        <div className="flex items-start gap-2 text-sm">
                            <Info size={14} className="mt-0.5 shrink-0" style={{ color: isGrok ? 'var(--accent-orange)' : 'var(--accent-purple)' }} />
                            <span className="text-[var(--text-secondary)]">
                                <strong>Why:</strong> {item.reason}
                            </span>
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
}

export default function Routing() {
    const [stats, setStats] = useState({});
    const [history, setHistory] = useState([]);
    const [rules, setRules] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, historyRes, logicRes] = await Promise.all([
                    getRoutingStats(),
                    getRoutingHistory(50),
                    api.get('/logic')
                ]);
                setStats(statsRes.data);
                setHistory(historyRes.data);
                setRules(logicRes.data.routing_triggers || {});
            } catch (error) {
                console.error('Failed to fetch routing data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(async () => {
            const [statsRes, historyRes] = await Promise.all([
                getRoutingStats(),
                getRoutingHistory(50),
            ]);
            setStats(statsRes.data);
            setHistory(historyRes.data);
        }, 10000);
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
        <div className="space-y-6 pb-12">
            <header className="lg:ml-0 ml-12">
                <h1 className="text-2xl font-bold">LLM Routing Engine</h1>
                <p className="text-[var(--text-secondary)]">Real-time decision logic between Grok (Street/Edgy) and Claude (Wise/Cultural).</p>
            </header>

            {/* How it works explainer */}
            <div className="card border-l-4" style={{ borderLeftColor: 'var(--accent-purple)' }}>
                <div className="flex items-start gap-3">
                    <Info size={18} className="mt-0.5 shrink-0" style={{ color: 'var(--accent-purple)' }} />
                    <div className="text-sm text-[var(--text-secondary)]">
                        <p className="font-semibold text-[var(--text-primary)] mb-1">How Routing Works</p>
                        <p>Each topic is scanned for Claude trigger keywords (cultural, proverbs, diaspora, etc.). The <strong>Cultural Relevance Score</strong> counts how many keywords were found.</p>
                        <ul className="mt-2 space-y-1 list-disc list-inside">
                            <li>Score <strong>≥ 2</strong> → <span style={{ color: 'var(--accent-purple)' }}>🧠 Claude</span> (High cultural depth required)</li>
                            <li>Score <strong>0–1</strong> → <span style={{ color: 'var(--accent-orange)' }}>⚡ Grok</span> (Standard/Edgy content)</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-[var(--bg-tertiary)]">
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
                        <div className="p-3 rounded-xl bg-[var(--bg-tertiary)]">
                            <Zap size={20} style={{ color: 'var(--accent-orange)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">⚡ Grok (Edgy)</p>
                            <p className="text-2xl font-bold">{stats.grok || 0}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-[var(--bg-tertiary)]">
                            <Sparkles size={20} style={{ color: 'var(--accent-purple)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">🧠 Claude (Wise)</p>
                            <p className="text-2xl font-bold">{stats.claude || 0}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Rules Sidebar (Right Column on desktop) */}
                <div className="lg:col-span-1 lg:order-last space-y-6">
                    <div className="card">
                        <div className="card-header mb-4">
                            <BookOpen size={20} />
                            <span>Claude Trigger Rules</span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] mb-4">
                            Content containing 2+ keywords from these categories routes to Claude. Otherwise, defaults to Grok.
                        </p>
                        <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                            {Object.entries(rules).map(([category, keywords]) => (
                                <div key={category}>
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-2">
                                        {category}
                                    </h4>
                                    <div className="flex flex-wrap gap-1.5">
                                        {keywords.map(kw => (
                                            <span key={kw} className={`px-2 py-0.5 rounded text-xs font-medium border bg-[var(--bg-tertiary)] text-[var(--text-primary)] border-[var(--bg-secondary)]`}>
                                                {kw}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="card">
                        <div className="card-header mb-2">
                            <GitBranch size={20} />
                            <span>Model Distribution</span>
                        </div>
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={50}
                                        outerRadius={70}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase()]} />
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
                        </div>
                    </div>
                </div>

                {/* Detailed History Table */}
                <div className="lg:col-span-2">
                    <div className="card">
                        <div className="card-header mb-4">
                            <GitBranch size={20} />
                            <span>Decision History</span>
                            <span className="text-xs text-[var(--text-secondary)] ml-auto font-normal">Click a row for details</span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-[var(--text-secondary)] uppercase bg-[var(--bg-tertiary)]">
                                    <tr>
                                        <th className="px-4 py-3 rounded-tl-lg">Time</th>
                                        <th className="px-4 py-3">Topic / Task</th>
                                        <th className="px-4 py-3">Persona</th>
                                        <th className="px-4 py-3" title="Number of Claude trigger keywords found in the topic">
                                            Cultural Relevance Score
                                        </th>
                                        <th className="px-4 py-3">Keywords Matched</th>
                                        <th className="px-4 py-3 rounded-tr-lg">Model Used</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.map((item) => (
                                        <DecisionRow key={item.id} item={item} />
                                    ))}
                                    {history.length === 0 && (
                                        <tr>
                                            <td colSpan="6" className="px-4 py-8 text-center text-[var(--text-secondary)]">
                                                No decisions recorded yet.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
