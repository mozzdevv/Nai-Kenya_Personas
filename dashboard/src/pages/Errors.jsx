import { useEffect, useState } from 'react';
import { getErrors } from '../api';
import { formatDualTime } from '../utils';
import { AlertTriangle, AlertCircle, Filter, RefreshCw, ShieldCheck } from 'lucide-react';

export default function Errors() {
    const [errors, setErrors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    const fetchErrors = async () => {
        setLoading(true);
        try {
            const level = filter === 'all' ? null : filter;
            const res = await getErrors(100, level);
            setErrors(res.data);
        } catch (error) {
            console.error('Failed to fetch errors:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchErrors();
        const interval = setInterval(fetchErrors, 60000);
        return () => clearInterval(interval);
    }, [filter]);

    const errorCount = errors.filter(e => e.level === 'error').length;
    const warningCount = errors.filter(e => e.level === 'warning').length;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4 lg:ml-0 ml-12">
                <h1 className="text-2xl font-bold">Error Logs</h1>

                <div className="flex items-center gap-4">
                    {/* Filter */}
                    <div className="flex items-center gap-2">
                        <Filter size={18} className="text-[var(--text-secondary)]" />
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="input w-32"
                        >
                            <option value="all">All</option>
                            <option value="error">Errors</option>
                            <option value="warning">Warnings</option>
                        </select>
                    </div>

                    {/* Refresh */}
                    <button
                        onClick={fetchErrors}
                        className="p-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[#333] transition-colors"
                    >
                        <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)' }}>
                            <AlertCircle size={20} style={{ color: 'var(--accent-red)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Errors</p>
                            <p className="text-2xl font-bold">{errorCount}</p>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)' }}>
                            <AlertTriangle size={20} style={{ color: 'var(--accent-orange)' }} />
                        </div>
                        <div>
                            <p className="text-sm text-[var(--text-secondary)]">Warnings</p>
                            <p className="text-2xl font-bold">{warningCount}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error List */}
            <div className="card">
                <div className="card-header">
                    <AlertTriangle size={20} />
                    <span>Log Entries</span>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="w-6 h-6 border-2 border-[var(--accent-green)] border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : errors.length === 0 ? (
                    <div className="text-center py-12 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--bg-secondary)]">
                        <div className="inline-flex p-4 rounded-full bg-green-900/20 mb-4">
                            <ShieldCheck size={48} className="text-[var(--accent-green)]" />
                        </div>
                        <h3 className="text-lg font-medium text-[var(--text-primary)]">System Healthy</h3>
                        <p className="text-[var(--text-secondary)] mt-1">No errors or warnings detected in the logs.</p>
                    </div>
                ) : (
                    <div className="space-y-3 max-h-[500px] overflow-auto">
                        {errors.map((error) => (
                            <div
                                key={error.id}
                                className={`p-4 rounded-lg border-l-4 ${error.level === 'error'
                                    ? 'bg-red-500/10 border-red-500'
                                    : 'bg-orange-500/10 border-orange-500'
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {error.level === 'error' ? (
                                            <AlertCircle size={16} className="text-red-400" />
                                        ) : (
                                            <AlertTriangle size={16} className="text-orange-400" />
                                        )}
                                        <span className={`badge ${error.level === 'error' ? 'badge-error' : 'badge-grok'}`}>
                                            {error.component}
                                        </span>
                                    </div>
                                    <span className="text-xs text-[var(--text-secondary)]">
                                        {formatDualTime(error.created_at)}
                                    </span>
                                </div>
                                <p className="text-sm mb-2">{error.message}</p>
                                {error.traceback && (
                                    <details className="mt-2">
                                        <summary className="text-xs text-[var(--text-secondary)] cursor-pointer hover:text-white">
                                            Show traceback
                                        </summary>
                                        <pre className="mt-2 p-2 rounded bg-black/30 text-xs overflow-auto max-h-40">
                                            {error.traceback}
                                        </pre>
                                    </details>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
