import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Users, Clock, Plug, Brain, Settings, User, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import ThemeToggle from './ThemeToggle';
import { useState } from 'react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/entities', icon: Users, label: 'Entities' },
  { to: '/automations', icon: Clock, label: 'Automations' },
  { to: '/integrations', icon: Plug, label: 'Integrations' },
  { to: '/memory', icon: Brain, label: 'Memory' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userInitials = (user?.full_name || user?.email || '')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <aside className="w-16 lg:w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold hidden lg:block">AI Agent</h1>
        <span className="text-lg font-bold lg:hidden block text-center">🤖</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            <Icon size={20} />
            <span className="hidden lg:inline text-sm">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Profile Section */}
      <div className="p-4 border-t border-gray-800 space-y-3">
        {/* Theme Toggle */}
        <ThemeToggle />

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-white"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
              {userInitials}
            </div>
            <span className="hidden lg:inline text-sm truncate">{user?.full_name || user?.email}</span>
          </button>

          {/* User Dropdown Menu */}
          {showUserMenu && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
              <NavLink
                to="/profile"
                onClick={() => setShowUserMenu(false)}
                className="flex items-center gap-3 w-full px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 transition-colors rounded-t-lg"
              >
                <User size={16} />
                <span className="hidden lg:inline text-sm">Profile</span>
              </NavLink>
              <button
                onClick={() => {
                  handleLogout();
                  setShowUserMenu(false);
                }}
                className="flex items-center gap-3 w-full px-4 py-2 text-red-400 hover:text-red-300 hover:bg-gray-700 transition-colors rounded-b-lg"
              >
                <LogOut size={16} />
                <span className="hidden lg:inline text-sm">Logout</span>
              </button>
            </div>
          )}
        </div>

        <p className="text-xs text-gray-600 hidden lg:block mt-3">Powered by Claude</p>
      </div>
    </aside>
  );
}
