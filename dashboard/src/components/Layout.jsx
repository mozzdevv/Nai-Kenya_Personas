import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    MessageSquare,
    Database,
    GitBranch,
    AlertTriangle,
    LogOut,
    Menu,
    X,
    ShieldCheck
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Overview' },
    { path: '/posts', icon: MessageSquare, label: 'Posts' },
    { path: '/rag', icon: Database, label: 'RAG Activity' },
    { path: '/knowledge', icon: Database, label: 'Knowledge Base' },
    { path: '/routing', icon: GitBranch, label: 'LLM Routing' },
    { path: '/validation', icon: ShieldCheck, label: 'Validation' },
    { path: '/logic', icon: GitBranch, label: 'Bot Logic' },
    { path: '/errors', icon: AlertTriangle, label: 'Errors' },
];

export default function Layout() {
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="min-h-screen flex">
            {/* Mobile menu button */}
            <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-[var(--bg-secondary)] lg:hidden"
            >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar */}
            <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-[var(--bg-secondary)] border-r border-[var(--bg-tertiary)]
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                {/* Logo */}
                <div className="p-6 border-b border-[var(--bg-tertiary)]">
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">🇰🇪</span>
                        <div>
                            <h1 className="font-bold text-lg">Nairobi Bots</h1>
                            <p className="text-xs text-[var(--text-secondary)]">Dashboard</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="p-4 flex-1">
                    <ul className="space-y-1">
                        {navItems.map((item) => (
                            <li key={item.path}>
                                <NavLink
                                    to={item.path}
                                    onClick={() => setSidebarOpen(false)}
                                    className={({ isActive }) => `
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive
                                            ? 'bg-[var(--accent-green)]/10 text-[var(--accent-green)]'
                                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-white'
                                        }
                  `}
                                >
                                    <item.icon size={20} />
                                    <span>{item.label}</span>
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </nav>

                {/* Logout */}
                <div className="p-4 border-t border-[var(--bg-tertiary)]">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-3 w-full rounded-lg
                       text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-white
                       transition-colors"
                    >
                        <LogOut size={20} />
                        <span>Logout</span>
                    </button>
                </div>
            </aside>

            {/* Mobile overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-30 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main content */}
            <main className="flex-1 p-4 lg:p-8 overflow-auto">
                <Outlet />
            </main>
        </div>
    );
}
