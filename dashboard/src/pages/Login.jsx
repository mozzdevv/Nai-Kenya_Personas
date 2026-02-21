import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';
import { Lock, User, AlertCircle } from 'lucide-react';

export default function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(username, password);
            localStorage.setItem('token', data.access_token);
            navigate('/');
        } catch (err) {
            setError('Invalid username or password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="card max-w-md w-full">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="text-4xl mb-2">🇰🇪</div>
                    <h1 className="text-2xl font-bold">Nairobi Bot Dashboard</h1>
                    <p className="text-[var(--text-secondary)] text-sm mt-1">
                        Monitor your X persona bots
                    </p>
                </div>

                {/* Error */}
                {error && (
                    <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-red-500/10 text-red-400">
                        <AlertCircle size={18} />
                        <span>{error}</span>
                    </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">Username</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" size={18} />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="input pl-10"
                                placeholder="Enter username"
                                required
                            />
                        </div>
                    </div>

                    <div className="mb-6">
                        <label className="block text-sm font-medium mb-2">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input pl-10"
                                placeholder="Enter password"
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary w-full flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Lock size={18} />
                                Sign In
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
