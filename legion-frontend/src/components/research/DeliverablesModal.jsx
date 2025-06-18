import { useState, useEffect } from 'react';
import { X, Download, FileText, ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react';
import PropTypes from 'prop-types';

const DeliverablesModal = ({ deliverables, isOpen, onClose, onDownload, initialIndex = 0 }) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    setCurrentIndex(initialIndex);
  }, [initialIndex, isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft' && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
      } else if (e.key === 'ArrowRight' && currentIndex < deliverables.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else if (e.key === 'f' || e.key === 'F') {
        setIsMaximized(!isMaximized);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentIndex, deliverables.length, onClose, isMaximized]);

  if (!isOpen || deliverables.length === 0) return null;

  const currentDeliverable = deliverables[currentIndex];

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-3xl"
        onClick={onClose}
      />
      
      {/* Modal Container */}
      <div className={`
        relative bg-[#1e1e1e]/95 backdrop-blur-2xl rounded-3xl shadow-2xl 
        flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-300 text-gray-100
        ${isMaximized ? 'w-[95vw] h-[95vh]' : 'w-full max-w-5xl h-[85vh] max-h-[900px]'}
        transition-all duration-500 ease-out border border-gray-700/20
      `}>
        
        {/* Floating Header Card */}
        <div className="relative p-4 pb-3">
          <div className="bg-[#252526]/80 backdrop-blur-xl rounded-xl border border-gray-700/30 shadow-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 min-w-0 flex-1">
                <div className="p-1.5 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <FileText className="w-4 h-4 text-blue-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="text-sm font-medium text-gray-50 truncate">
                    {currentDeliverable.title}
                  </h2>
                  <div className="flex items-center space-x-1.5 mt-1">
                    <span className="text-xs font-medium uppercase px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded-md border border-blue-500/20">
                      {currentDeliverable.type}
                    </span>
                    <span className="text-xs text-gray-500 px-1.5 py-0.5 bg-gray-700/50 rounded-md">
                      {currentDeliverable.size}
                    </span>
                    <span className="text-xs text-gray-500 px-1.5 py-0.5 bg-gray-700/50 rounded-md">
                      {formatDate(currentDeliverable.created)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Header Actions */}
              <div className="flex items-center space-x-1.5">
                {/* Navigation for multiple deliverables */}
                {deliverables.length > 1 && (
                  <>
                    <div className="flex items-center space-x-1.5 px-2 py-1 bg-[#252526]/60 backdrop-blur-lg rounded-lg border border-gray-700/30">
                      <span className="text-xs text-gray-400 font-medium">
                        {currentIndex + 1} of {deliverables.length}
                      </span>
                    </div>
                    <button
                      onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                      disabled={currentIndex === 0}
                      className="p-1.5 bg-[#252526]/60 backdrop-blur-lg hover:bg-gray-600/60 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 rounded-lg transition-all duration-200 border border-gray-700/30 hover:scale-105"
                      title="Previous deliverable"
                    >
                      <ChevronLeft size={14} />
                    </button>
                    <button
                      onClick={() => setCurrentIndex(Math.min(deliverables.length - 1, currentIndex + 1))}
                      disabled={currentIndex === deliverables.length - 1}
                      className="p-1.5 bg-[#252526]/60 backdrop-blur-lg hover:bg-gray-600/60 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 rounded-lg transition-all duration-200 border border-gray-700/30 hover:scale-105"
                      title="Next deliverable"
                    >
                      <ChevronRight size={14} />
                    </button>
                  </>
                )}

                <button
                  onClick={() => onDownload(currentDeliverable)}
                  className="p-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg transition-all duration-200 border border-blue-500/30 hover:scale-105"
                  title="Download"
                >
                  <Download size={14} />
                </button>

                <button
                  onClick={() => setIsMaximized(!isMaximized)}
                  className="p-1.5 bg-[#252526]/60 backdrop-blur-lg hover:bg-gray-600/60 text-gray-300 rounded-lg transition-all duration-200 border border-gray-700/30 hover:scale-105"
                  title={isMaximized ? "Restore" : "Maximize"}
                >
                  {isMaximized ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                </button>

                <button
                  onClick={onClose}
                  className="p-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-all duration-200 border border-red-500/30 hover:scale-105"
                  title="Close"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-4 pb-3 thin-scrollbar relative">
          {/* Top gradient fade */}
          <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-[#1e1e1e] to-transparent pointer-events-none z-10"></div>
          
          {currentDeliverable.content ? (
            <div className="bg-[#252526]/60 backdrop-blur-lg rounded-xl border border-gray-700/30 shadow-lg p-4 mt-2">
              <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed">
                {currentDeliverable.content}
              </pre>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="p-4 bg-[#252526]/60 backdrop-blur-lg rounded-xl mb-3 border border-gray-700/30">
                  <FileText size={32} className="text-gray-500 mx-auto" />
                </div>
                <p className="text-base font-medium text-gray-300 mb-1">No preview available</p>
                <p className="text-sm text-gray-500">Download to view this file</p>
              </div>
            </div>
          )}
          
          {/* Bottom gradient fade */}
          <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-[#1e1e1e] to-transparent pointer-events-none z-10"></div>
        </div>

        {/* Floating Footer Card */}
        <div className="relative p-4 pt-2">
          <div className="bg-[#252526]/60 backdrop-blur-xl rounded-lg border border-gray-700/30 shadow-lg p-2.5">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-800/60 rounded text-xs font-medium">ESC</kbd>
                  <span>Close</span>
                </span>
                {deliverables.length > 1 && (
                  <span className="flex items-center space-x-1">
                    <kbd className="px-1.5 py-0.5 bg-gray-800/60 rounded text-xs font-medium">←→</kbd>
                    <span>Navigate</span>
                  </span>
                )}
                <span className="flex items-center space-x-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-800/60 rounded text-xs font-medium">F</kbd>
                  <span>Fullscreen</span>
                </span>
              </div>
              <div className="flex items-center space-x-1.5">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400 font-medium">Ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

DeliverablesModal.propTypes = {
  deliverables: PropTypes.arrayOf(PropTypes.shape({
    title: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    size: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    created: PropTypes.string.isRequired,
    content: PropTypes.string
  })).isRequired,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onDownload: PropTypes.func.isRequired,
  initialIndex: PropTypes.number
};

export default DeliverablesModal;