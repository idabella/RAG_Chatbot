// src/components/common/Sidebar.tsx - Correction des bugs
import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  ChatBubbleLeftRightIcon, 
  PlusIcon, 
  DocumentArrowUpIcon,
  CogIcon,
  HomeIcon,
  ChevronLeftIcon,
  Bars3Icon
} from '@heroicons/react/24/outline';
import { useChat } from '../../contexts/ChatProvider';

const Sidebar: React.FC = () => {
  const { conversations, newChat, deleteChat, currentChatId, setCurrentChatId } = useChat();
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Fonction pour créer un nouveau chat et naviguer
  const handleNewChat = () => {
    newChat();
    navigate('/chat');
  };

  // Fonction pour sélectionner une conversation et naviguer
  const handleSelectConversation = (conversationId: string) => {
    setCurrentChatId(conversationId);
    navigate('/chat');
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Mettre à jour la variable CSS à chaque changement d'état
  useEffect(() => {
    document.documentElement.style.setProperty('--sidebar-width', isCollapsed ? '64px' : '256px');
  }, [isCollapsed]);

  return (
    <div 
      className={`fixed top-0 left-0 flex flex-col h-full text-white border border-gray-800 rounded-xl bg-gradient-to-br from-gray-950 to-gray-900 transition-all duration-300 z-50 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
      style={{
        '--sidebar-width': isCollapsed ? '64px' : '256px'
      } as React.CSSProperties}
    >
      
      {/* Header avec logo et bouton toggle - Toujours visible */}
      <div className="flex items-center justify-between flex-shrink-0 p-4 border-b border-zinc-700 min-h-[72px]">
        <div className="flex items-center flex-1 min-w-0">
        {!isCollapsed ? (
          <h1 
            className="text-3xl font-extrabold bg-gradient-to-r from-white via-[#e8d5ff] to-[#c084fc] text-transparent bg-clip-text font-[Poppins] truncate pl-5"
            style={{
              filter: 'drop-shadow(0 0 12px rgba(192, 132, 252, 0.6)) drop-shadow(0 0 24px rgba(192, 132, 252, 0.3))'
            }}
          >
            FileChat
          </h1>
        ) : (
          <div className="flex items-center justify-center flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600">
            <span className="font-bold text-white">F</span>
          </div>
        )}
      </div>
        
        {/* Bouton toggle - Toujours visible avec position fixe */}
        <button
          onClick={toggleSidebar}
          className="flex items-center justify-center flex-shrink-0 w-8 h-8 ml-2 text-gray-400 transition-all duration-200 rounded-lg hover:text-white hover:bg-gray-800"
          title={isCollapsed ? "Ouvrir la sidebar" : "Fermer la sidebar"}
          type="button"
        >
          {isCollapsed ? (
            <Bars3Icon className="w-5 h-5" />
          ) : (
            <ChevronLeftIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="flex-shrink-0 p-4">
        <button
          onClick={handleNewChat}
          className={`w-full flex items-center justify-center px-3 py-3 bg-blue-700 hover:bg-blue-600 rounded-lg transition-all duration-200 hover:scale-[1.02] ${
            isCollapsed ? '' : 'space-x-3'
          }`}
          title={isCollapsed ? "Nouvelle Chat" : ""}
          type="button"
        >
          <PlusIcon className="flex-shrink-0 w-5 h-5" />
          {!isCollapsed && <span className="font-medium">Nouvelle Chat</span>}
        </button>
      </div>

      {/* Conversations History - Seulement si pas collapsed */}
      {!isCollapsed && (
        <div className="flex-1 min-h-0 px-4 overflow-y-auto">
          <div className="space-y-2">
            {conversations.length > 0 ? (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => handleSelectConversation(conversation.id)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-zinc-800 ${
                    currentChatId === conversation.id ? 'bg-zinc-800 border border-zinc-600' : ''
                  }`}
                >
                  <div className="flex items-center flex-1 min-w-0 space-x-3">
                    <ChatBubbleLeftRightIcon className="flex-shrink-0 w-4 h-4 text-zinc-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{conversation.title}</p>
                      <p className="text-xs truncate text-zinc-400">{conversation.lastMessage}</p>
                    </div>
                  </div>
                  {currentChatId === conversation.id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(conversation.id);
                      }}
                      className="flex-shrink-0 ml-2 transition-colors duration-200 text-zinc-400 hover:text-red-400"
                      type="button"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-zinc-500">
                <p className="text-sm">Aucune conversation</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="flex-shrink-0 p-4 space-y-2 border-t border-zinc-700">
        <NavLink
          to="/chat"
          className={({ isActive }) =>
            `flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 hover:bg-zinc-800 ${
              isActive ? 'bg-zinc-800' : ''
            }`
          }
          title={isCollapsed ? "Chat" : ""}
        >
          <ChatBubbleLeftRightIcon className="flex-shrink-0 w-5 h-5" />
          {!isCollapsed && <span>Chat</span>}
        </NavLink>

        <NavLink
          to="/"
          className={({ isActive }) =>
            `flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 hover:bg-zinc-800 ${
              isActive ? 'bg-zinc-800' : ''
            }`
          }
          title={isCollapsed ? "Accueil" : ""}
        >
          <HomeIcon className="flex-shrink-0 w-5 h-5" />
          {!isCollapsed && <span>Accueil</span>}
        </NavLink>
        
        <NavLink
          to="/upload"
          className={({ isActive }) =>
            `flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 hover:bg-zinc-800 ${
              isActive ? 'bg-zinc-800' : ''
            }`
          }
          title={isCollapsed ? "Upload Document" : ""}
        >
          <DocumentArrowUpIcon className="flex-shrink-0 w-5 h-5" />
          {!isCollapsed && <span>Upload Document</span>}
        </NavLink>
        
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 hover:bg-zinc-800 ${
              isActive ? 'bg-zinc-800' : ''
            }`
          }
          title={isCollapsed ? "Paramètres" : ""}
        >
          <CogIcon className="flex-shrink-0 w-5 h-5" />
          {!isCollapsed && <span>Paramètres</span>}
        </NavLink>
      </div>
    </div>
  );
};

export default Sidebar;