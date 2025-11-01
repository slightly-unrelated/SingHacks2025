import { Link, useLocation } from 'react-router-dom';

const Header = () => {
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/transactions', label: 'Transaction Monitoring' },
    { path: '/documents', label: 'Document Analysis' },
    { path: '/cross-reference', label: 'Cross-Reference' },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-primary-navy text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="font-serif text-2xl font-semibold tracking-tight">
              Julius Bär
            </div>
            <div className="h-6 w-px bg-white/30"></div>
            <div className="text-sm font-light tracking-wide">
              AML Monitor
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors duration-200 ${
                  isActive(link.path)
                    ? 'bg-white/10 text-white'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* User Section */}
          <div className="flex items-center space-x-3">
            <div className="text-sm text-right">
              <div className="font-medium">Compliance Officer</div>
              <div className="text-xs text-white/60">View Only</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <span className="text-sm font-medium">CO</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
