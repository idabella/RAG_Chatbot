import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UserIcon, CogIcon} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';

interface HeaderProps {
  showSidebar?: boolean;
}

const Header: React.FC<HeaderProps> = ({ showSidebar = true }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/'); // Redirection vers la homepage
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      // En cas d'erreur, on redirige quand même vers la homepage
      navigate('/');
    }
  };

  return (
    <header className="px-6 py-4 border-b border-gray-800 bg-gradient-to-b from-gray-950 to-gray-900 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {!showSidebar && (
            <h1 className="text-2xl font-bold text-transparent bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text">
              FileChat
            </h1>
          )}
        </div>
                
        <div className="flex items-center space-x-4">
          
                    
          {user && (
            <div className="flex items-center space-x-3">
              <div className="flex items-center pr-20 space-x-2">
                <UserIcon className="w-6 h-6 text-gray-200" />
                <span className="text-sm font-medium text-gray-500">{user.name}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-white transition-colors duration-200 hover:text-gray-700"
              >
                <span className="material-symbols-outlined">
                logout
                </span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;