import { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Search } from 'lucide-react';
import ChatInput from './ChatInput';
import ChatBubble from './ChatBubble';
import { getChatById, saveMessage } from '../../services/MainChatArea-api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

export default function MainChatArea({ 
  sidebarOpen, 
  onOpenResearch, 
  currentChatId,
  onMissionEvent
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isConsulThinking, setIsConsulThinking] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket setup
  useEffect(() => {
    if (currentChatId) {
      setupWebSocket(currentChatId);
      loadChat(currentChatId);
    } else {
      setMessages([]);
      closeWebSocket();
    }

    return () => {
      closeWebSocket();
    };
  }, [currentChatId]);

  const setupWebSocket = (chatId) => {
    closeWebSocket();    const wsUrl = `${WS_BASE_URL}/ws/${chatId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log(`WebSocket connected for chat ${chatId}`);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        if (data.event === 'consul_thinking') {
          setIsConsulThinking(true);
        } else if (data.event === 'consul_response') {
          setIsConsulThinking(false);
          
          const aiMessage = {
            id: Date.now().toString(),
            content: data.message,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            agent: data.agent,
            requires_response: data.requires_response,
            mission_plan: data.mission_plan
          };
          
          setMessages(prev => [...prev, aiMessage]);
        }
        else if (data.event === 'mission_initiated' || 
                 data.event === 'mission_complete' || 
                 data.event === 'mission_error' || 
                 data.event === 'mission_stopped') {
          if (onMissionEvent) {
            onMissionEvent(data);
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConsulThinking(false);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConsulThinking(false);
    };
  };

  const closeWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const loadChat = async (chatId) => {
    setLoading(true);
    try {
      const chat = await getChatById(chatId);
      setMessages(chat.messages || []);
    } catch (error) {
      console.error('Error loading chat:', error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (messageText) => {
    if (!currentChatId) {
      console.error('No current chat ID');
      return;
    }

    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      await saveMessage(currentChatId, userMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    }
  };

  return (
    <div className="flex-1 h-screen bg-[#292a2d] flex flex-col text-gray-300 relative">
      {/* Research Button */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={onOpenResearch}
          disabled={!currentChatId}
          className={`flex items-center justify-center p-1.5 rounded-full transition-colors ${
            !currentChatId ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'
          }`}
          title="Open Research"
        >
          <Search size={16} />
        </button>
      </div>

      {/* Chat Messages Area - Now takes full height */}
      <div className="flex-1 overflow-y-auto thin-scrollbar pb-32">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading chat...</div>
          </div>
        ) : messages.length > 0 || isConsulThinking ? (
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {messages.map(message => (
              <ChatBubble
                key={message.id}
                message={message.content}
                isUser={message.role === 'user'}
                timestamp={message.timestamp}
                agent={message.agent}
              />
            ))}
            
            {isConsulThinking && (
              <div className="flex w-full mb-3 sm:mb-4 justify-start">
                <div className="max-w-[85%] sm:max-w-[70%] md:max-w-[65%]">
                  <div className="px-4 py-2.5">
                    <p className="text-gray-100 text-sm leading-relaxed">
                      <span className="text-blue-400">CONSUL:</span> Understanding your request...
                      <span className="animate-pulse">●●●</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <h1
              className="text-3xl sm:text-4xl font-medium mb-1 animate-fade-in text-gray-400"
              style={{ fontFamily: "'Inter', sans-serif" }}
            >
              Hello, I'm{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600 uppercase drop-shadow-lg">
                Legion
              </span>.
            </h1>
            <p className="text-gray-500 text-sm mb-4">Your Strategic Research employee</p>
            {!currentChatId && (
              <p className="text-gray-500 text-sm">Start a new chat to begin</p>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Chat Input - Fixed at bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#292a2d] via-[#292a2d]/95 to-transparent pt-8 pb-4 sm:pb-6">
        <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <ChatInput
            onSendMessage={handleSendMessage}
            hasMessages={messages.length > 0}
            disabled={!currentChatId || isConsulThinking}
          />
          <p className="text-center text-xs text-gray-500 mt-2">Powered by Gemini 2.5</p>
        </div>
      </div>
    </div>
  );
}

MainChatArea.propTypes = {
  sidebarOpen: PropTypes.bool.isRequired,
  onOpenResearch: PropTypes.func.isRequired,
  currentChatId: PropTypes.string,
  onMissionEvent: PropTypes.func,
};