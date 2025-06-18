import { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Reply, 
  AtSign, 
  MessageCircle,
  Crown,        // CONSUL - Director/Leader
  Search,       // CENTURION - Data Searcher
  FileText,     // SCRIBE - Document Writer
  TrendingUp,   // AUGUR - Analyst/Predictor
  Settings      // SYSTEM - System Operations
} from 'lucide-react';
import { streamAgentComms } from '../../services/ResearchDashboard-api.js';

const AgentComms = ({ chatId }) => {
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  // Agent icon mapping based on their roles
  const getAgentIcon = (agentName) => {
    const iconMap = {
      CONSUL: Crown,        // Director/Orchestrator - Crown represents leadership
      CENTURION: Search,    // Data Searcher - Search icon for finding data
      SCRIBE: FileText,     // Writer - Document icon for content creation
      AUGUR: TrendingUp,    // Analyst - Trending chart for analysis/prediction
      SYSTEM: Settings      // System - Settings gear for system operations
    };
    return iconMap[agentName] || Settings;
  };

  // Define agent colors for message styling
  const agentColors = {
    CONSUL: "bg-purple-500/10 border-purple-500/20 text-purple-100",
    CENTURION: "bg-blue-500/10 border-blue-500/20 text-blue-100",
    AUGUR: "bg-emerald-500/10 border-emerald-500/20 text-emerald-100",
    SCRIBE: "bg-amber-500/10 border-amber-500/20 text-amber-100",
    SYSTEM: "bg-gray-500/10 border-gray-500/20 text-gray-100"
  };

  const agentAccentColors = {
    CONSUL: "text-purple-400",
    CENTURION: "text-blue-400",
    AUGUR: "text-emerald-400",
    SCRIBE: "text-amber-400",
    SYSTEM: "text-gray-400"
  };

  const agentIconColors = {
    CONSUL: "text-purple-400 bg-purple-500/20",
    CENTURION: "text-blue-400 bg-blue-500/20",
    AUGUR: "text-emerald-400 bg-emerald-500/20",
    SCRIBE: "text-amber-400 bg-amber-500/20",
    SYSTEM: "text-gray-400 bg-gray-500/20"
  };

  // Stream agent comms
  useEffect(() => {
    if (!chatId) return;

    const cleanup = streamAgentComms(chatId, (newMessages) => {
      setMessages(newMessages);
    });

    return cleanup;
  }, [chatId]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Format time
  const formatTime = (timeString) => {
    if (!timeString) return '';
    try {
      const date = new Date(timeString);
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return timeString;
    }
  };

  // Get message type styling
  const getMessageTypeStyle = (msg) => {
    switch (msg.type) {
      case 'thinking':
        return 'italic text-gray-400 bg-gray-700/30 border-gray-600/30 px-2 py-1 rounded';
      case 'system_announcement':
      case 'workflow_announcement':
        return 'font-medium border-l-4 border-l-blue-500 pl-3 bg-blue-500/5';
      case 'deliverable_announcement':
        return 'font-medium border-l-4 border-l-green-500 pl-3 bg-green-500/5 text-green-300';
      case 'question_completion':
        return 'font-medium border-l-4 border-l-emerald-500 pl-3 bg-emerald-500/5 text-emerald-300';
      case 'question_start':
        return 'font-medium border-l-4 border-l-cyan-500 pl-3 bg-cyan-500/5 text-cyan-300';
      default:
        return '';
    }
  };

  const uniqueAgents = [...new Set(messages.map(msg => msg.agent || msg.from_agent || 'SYSTEM'))];

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] text-gray-100">
      
      {/* Compact Floating Header */}
      <div className="relative p-4 pb-3">
        <div className="bg-[#252526]/90 backdrop-blur-xl rounded-xl border border-gray-700/40 shadow-2xl p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/60"></div>
              <h2 className="text-sm font-semibold text-gray-50 tracking-tight">Agent Communications</h2>
              
              {/* Compact Agent Icons Group */}
              <div className="flex items-center -space-x-1 ml-2">
                {uniqueAgents.slice(0, 4).map((agentName, index) => {
                  const IconComponent = getAgentIcon(agentName);
                  return (
                    <div key={agentName} className="relative" style={{ zIndex: 10 - index }}>
                      <div className={`
                        w-5 h-5 rounded-full border-2 border-[#252526] flex items-center justify-center
                        ${agentIconColors[agentName] || agentIconColors.SYSTEM}
                      `}>
                        <IconComponent className="w-2.5 h-2.5" />
                      </div>
                    </div>
                  );
                })}
                {uniqueAgents.length > 4 && (
                  <div className="w-5 h-5 rounded-full bg-gray-600/80 border-2 border-[#252526] flex items-center justify-center text-xs font-bold text-gray-300">
                    +{uniqueAgents.length - 4}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-1.5 text-xs">
              <div className="flex items-center space-x-1">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                <span className="text-green-400 font-medium">
                  {uniqueAgents.length}
                </span>
              </div>
              <span className="px-2 py-0.5 bg-gray-500/15 text-gray-400 rounded-md font-medium border border-gray-500/20">
                {messages.length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2.5 thin-scrollbar">
        {messages.length > 0 ? (
          messages.map((msg, index) => {
            const fromAgent = msg.agent || msg.from_agent || 'SYSTEM';
            const toAgent = msg.to_agent;
            const isDirectMessage = !!toAgent;
            const IconComponent = getAgentIcon(fromAgent);

            return (
              <div key={msg.id || index} className="group">
                <div className={`
                  flex items-start space-x-3 relative p-3.5 rounded-xl shadow-lg transition-all duration-200 backdrop-blur-lg border
                  ${agentColors[fromAgent] || agentColors.SYSTEM}
                  hover:shadow-xl hover:border-opacity-60 hover:scale-[1.01]
                `}>
                  
                  {/* Agent Icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    <div className={`
                      w-7 h-7 rounded-full flex items-center justify-center border-2 border-opacity-30
                      ${agentIconColors[fromAgent] || agentIconColors.SYSTEM}
                      ${fromAgent === 'CONSUL' ? 'border-purple-400' :
                        fromAgent === 'CENTURION' ? 'border-blue-400' :
                        fromAgent === 'AUGUR' ? 'border-emerald-400' :
                        fromAgent === 'SCRIBE' ? 'border-amber-400' :
                        'border-gray-400'}
                    `}>
                      <IconComponent className="w-4 h-4" />
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    {/* Agent Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-semibold ${agentAccentColors[fromAgent] || agentAccentColors.SYSTEM}`}>
                          {fromAgent}
                        </span>
                        {toAgent && (
                          <>
                            <AtSign className="w-3 h-3 text-gray-500" />
                            <span className={`text-sm font-medium ${agentAccentColors[toAgent] || 'text-gray-400'}`}>
                              {toAgent}
                            </span>
                          </>
                        )}
                      </div>
                      
                      <span className="text-xs text-gray-500 bg-gray-800/60 px-2 py-1 rounded-md border border-gray-600/30 font-mono">
                        {formatTime(msg.time)}
                      </span>
                    </div>

                    {/* Message Content */}
                    <div className={`
                      text-sm text-gray-200 leading-relaxed
                      ${getMessageTypeStyle(msg)}
                    `}>
                      {msg.message || msg.raw_message}
                    </div>

                    {/* Message Context */}
                    <div className="flex items-center space-x-2 mt-2.5">
                      {/* Question ID badge */}
                      {msg.question_id && (
                        <span className="text-xs text-cyan-400 font-mono bg-cyan-500/15 px-1.5 py-0.5 rounded border border-cyan-500/30">
                          Q#{msg.question_id}
                        </span>
                      )}
                      
                      {/* Conversation type badge */}
                      {msg.conversation_type && msg.conversation_type !== 'chat' && (
                        <span className="text-xs text-purple-400 font-medium bg-purple-500/15 px-2 py-0.5 rounded border border-purple-500/30">
                          {msg.conversation_type.replace('_', ' ')}
                        </span>
                      )}
                      
                      {/* Response indicator */}
                      {msg.requires_response && (
                        <div className="flex items-center space-x-1.5 bg-orange-500/15 px-2 py-1 rounded border border-orange-500/30">
                          <div className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-pulse"></div>
                          <span className="text-xs text-orange-400 font-medium">response needed</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Connection indicator for direct messages */}
                  {isDirectMessage && (
                    <div className="absolute -left-4 top-1/2 transform -translate-y-1/2">
                      <div className="w-4 h-px bg-gradient-to-r from-gray-600 to-transparent"></div>
                      <div className="w-1.5 h-1.5 bg-gray-600 rounded-full -mt-0.5"></div>
                    </div>
                  )}
                  
                  {/* Subtle hover glow */}
                  <div className={`
                    absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none
                    ${fromAgent === 'CONSUL' ? 'bg-gradient-to-r from-purple-500/5 to-purple-400/5' :
                      fromAgent === 'CENTURION' ? 'bg-gradient-to-r from-blue-500/5 to-blue-400/5' :
                      fromAgent === 'AUGUR' ? 'bg-gradient-to-r from-emerald-500/5 to-emerald-400/5' :
                      fromAgent === 'SCRIBE' ? 'bg-gradient-to-r from-amber-500/5 to-amber-400/5' :
                      'bg-gradient-to-r from-gray-500/5 to-gray-400/5'}
                  `} />
                </div>
              </div>
            );
          })
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 py-12">
            <div className="p-5 bg-[#252526]/70 backdrop-blur-lg rounded-xl mb-3 border border-gray-700/40 shadow-lg">
              <MessageCircle className="w-7 h-7 text-gray-400" />
            </div>
            <p className="text-sm font-medium mb-1 text-gray-300">No messages yet</p>
            <p className="text-xs text-gray-500 max-w-48 leading-relaxed">Agent communications will appear here</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default AgentComms;