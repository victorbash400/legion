import React, { useState, useEffect, useRef } from 'react';
import { ArrowUp } from 'lucide-react';
import PropTypes from 'prop-types';

function ChatInput({ onSendMessage, hasMessages }) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = parseInt(textareaRef.current.style.maxHeight || '120', 10);
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`w-full ${hasMessages ? 'pb-2 sm:pb-3' : 'pb-6 sm:pb-8'}`}>
      <div className="max-w-xl mx-auto px-2 sm:px-0">
        <div className="relative">
          {/* Main input container with Legion-like blue border */}
          <div className="relative bg-[#292a2d] rounded-2xl shadow-xl border border-blue-500"> {/* Changed border-gray-700 to border-blue-500 */}
            <div className="flex items-end p-2 gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="How may I help you?" // Updated placeholder
                  className="w-full px-3 py-2.5 bg-transparent border-0 resize-none focus:outline-none text-gray-200 placeholder-gray-500 text-base font-normal leading-snug"
                  rows="1"
                  style={{
                    minHeight: '52px',
                    maxHeight: '120px',
                    paddingTop: '13px',
                    paddingBottom: '13px',
                  }}
                />
              </div>
              <div className="flex-shrink-0">
                <button
                  onClick={handleSubmit}
                  disabled={!message.trim()}
                  className="h-9 w-9 bg-blue-600 text-white !rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 !border-none !p-0"
                  aria-label="Send message"
                >
                  <ArrowUp className="w-4 h-4" strokeWidth={2.25} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

ChatInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  hasMessages: PropTypes.bool.isRequired,
};

export default ChatInput;