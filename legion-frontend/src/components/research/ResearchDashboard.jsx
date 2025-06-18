import { useState } from 'react';
import { X } from 'lucide-react';
import PropTypes from 'prop-types';
import TasksOrders from './TasksOrders';
import AgentWorkspace from './AgentWorkspace';
import AgentComms from './AgentComms';

const ResearchDashboard = ({ chatId, onClose, missionStatus }) => {
  // Add debug logging to see what's being passed
  console.log('ResearchDashboard received chatId:', chatId, 'Type:', typeof chatId);
  
  // More explicit check for chatId
  if (!chatId || chatId === null || chatId === undefined || chatId === '') {
    console.log('No valid chatId provided to ResearchDashboard');
    return (
      <div className="flex h-screen items-center justify-center bg-[#1e1e1e] text-gray-300">
        <div className="text-center">
          <p className="text-lg font-light">Please select a chat to view research dashboard.</p>
          <p className="text-sm text-gray-500 mt-2">
            Received chatId: {String(chatId)} (type: {typeof chatId})
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#1e1e1e] text-gray-300 gap-0">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-5 right-5 z-40 p-2.5 bg-[#252526]/80 backdrop-blur-xl hover:bg-gray-700 rounded-xl transition-all duration-200 shadow-lg"
        aria-label="Close Research Dashboard"
      >
        <X size={18} className="text-gray-300" />
      </button>

      {/* Left Panel - Tasks & Orders */}
      <div className="w-80 h-full overflow-hidden">
        <TasksOrders chatId={chatId} />
      </div>

      {/* Center Panel - Agent Comms */}
      <div className="flex-1 h-full overflow-hidden">
        <AgentComms chatId={chatId} />
      </div>

      {/* Right Panel - Agent Workspace */}
      <div className="w-96 h-full overflow-hidden">
        <AgentWorkspace chatId={chatId} />
      </div>
    </div>
  );
};

ResearchDashboard.propTypes = {
  chatId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  missionStatus: PropTypes.string,
};

export default ResearchDashboard;