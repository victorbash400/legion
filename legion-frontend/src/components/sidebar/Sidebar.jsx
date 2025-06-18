import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { PlusSquare, ChevronDown, ChevronUp } from 'lucide-react';
import { createNewChat, getAllChats } from '../../services/MainChatArea-api';

// Helper component for sidebar items for better readability and reusability
const SidebarItem = ({ icon: Icon, text, isOpen, isHeader = false, onClick, isActive = false, showIconWhenClosed = true }) => (
  <div
    onClick={onClick}
    role={onClick ? "button" : undefined}
    tabIndex={onClick ? 0 : undefined}
    onKeyPress={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    className={`flex items-center rounded-lg cursor-pointer transition-all duration-200 group
                 ${isHeader && isOpen ? 'mt-4 mb-1 px-3 py-2 text-xs text-gray-400 uppercase tracking-wider' : 'px-3 py-2 hover:bg-[#2a2d30] hover:shadow-sm'}
                 ${isActive && !isHeader ? 'bg-[#2a2d30] shadow-sm' : ''}
                 ${!isOpen && !isHeader ? 'justify-center px-2 py-2' : ''}
                 ${!isOpen && !showIconWhenClosed ? 'hidden' : ''}
               `}
    aria-label={text}
  >
    {Icon && (
      <div className={`flex items-center justify-center shrink-0
        ${isHeader ? 'text-gray-400' : 'text-gray-400 group-hover:text-gray-200 transition-colors duration-200'}
        ${isActive && !isHeader ? 'text-gray-200' : ''}
        ${isOpen && !isHeader ? 'w-5 h-5 mr-3' : 'w-5 h-5'}
      `}>
        <Icon size={16} />
      </div>
    )}
    {isOpen && (
      <span className={`text-sm truncate
        ${isHeader ? 'font-medium' : 'text-gray-300 group-hover:text-gray-100 transition-colors duration-200'} 
        ${isActive && !isHeader ? 'text-gray-100' : ''}
      `}>
        {text}
      </span>
    )}
  </div>
);

SidebarItem.propTypes = {
  icon: PropTypes.elementType,
  text: PropTypes.string.isRequired,
  isOpen: PropTypes.bool.isRequired,
  isHeader: PropTypes.bool,
  onClick: PropTypes.func,
  isActive: PropTypes.bool,
  showIconWhenClosed: PropTypes.bool,
};

export default function Sidebar({ isOpen, onHover, currentChatId, onChatSelect, onNewChat }) {
  const [showMoreHistory, setShowMoreHistory] = useState(false);
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load chats on component mount
  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    setLoading(true);
    try {
      const chatList = await getAllChats();
      setChats(chatList);
    } catch (error) {
      console.error('Error loading chats:', error);
      setChats([]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const newChat = await createNewChat();
      setChats(prev => [newChat, ...prev]); // Add new chat to the beginning
      onNewChat(newChat.chatId);
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  const visibleHistoryItems = showMoreHistory ? chats : chats.slice(0, 5);

  return (
    <div
      className={`h-full transition-all duration-300 ease-in-out shrink-0 bg-[#1f2023] text-white flex flex-col
                   ${isOpen ? 'w-72' : 'w-16'}`}
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
    >
      <div className="px-2 py-4 flex flex-col h-full">
        {/* New Chat */}
        <SidebarItem
          icon={PlusSquare}
          text="New chat"
          isOpen={isOpen}
          onClick={handleNewChat}
          isActive={false}
          showIconWhenClosed={true}
        />

        {/* History Section - Only show when sidebar is open */}
        {isOpen && (
          <>
            <SidebarItem text="History" isOpen={isOpen} isHeader />

            <div className="overflow-y-auto flex-grow">
              {loading ? (
                <div className="px-3 py-2 text-sm text-gray-400">Loading chats...</div>
              ) : visibleHistoryItems.length > 0 ? (
                <>
                  {visibleHistoryItems.map((chat) => (
                    <SidebarItem
                      key={chat.chatId}
                      text={chat.title || 'New Chat'}
                      isOpen={isOpen}
                      onClick={() => onChatSelect(chat.chatId)}
                      isActive={currentChatId === chat.chatId}
                      showIconWhenClosed={false}
                    />
                  ))}

                  {chats.length > 5 && (
                    <div
                      onClick={() => setShowMoreHistory(!showMoreHistory)}
                      role="button"
                      tabIndex={0}
                      onKeyPress={(e) => e.key === 'Enter' && setShowMoreHistory(!showMoreHistory)}
                      className="flex items-center px-3 py-2 rounded-lg hover:bg-[#2a2d30] hover:shadow-sm cursor-pointer transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-center shrink-0 w-5 h-5 mr-3">
                        {showMoreHistory ?
                          <ChevronUp size={16} className="text-gray-400 group-hover:text-gray-200 transition-colors duration-200" /> :
                          <ChevronDown size={16} className="text-gray-400 group-hover:text-gray-200 transition-colors duration-200" />
                        }
                      </div>
                      <span className="text-sm text-gray-300 group-hover:text-gray-100 transition-colors duration-200">
                        {showMoreHistory ? 'Show less' : 'Show more'}
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <div className="px-3 py-2 text-sm text-gray-400">No chat history</div>
              )}
            </div>
          </>
        )}

        {/* Spacer to push content to the bottom if needed */}
        <div className="flex-grow"></div>
      </div>
    </div>
  );
}

Sidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onHover: PropTypes.func.isRequired,
  currentChatId: PropTypes.string,
  onChatSelect: PropTypes.func.isRequired,
  onNewChat: PropTypes.func.isRequired,
};