import { useState, useEffect, useRef } from 'react';
import { Clock, Activity, FileText, Download, ExternalLink, Zap, Brain } from 'lucide-react';
import { streamOperations } from '../../services/ResearchDashboard-api.js';
import { getDeliverables } from '../../services/deliverables-api';
import PropTypes from 'prop-types';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

const AgentWorkspace = ({ chatId }) => {
  const [activeOperations, setActiveOperations] = useState([]);
  const [deliverables, setDeliverables] = useState([]);
  const [loadingDeliverables, setLoadingDeliverables] = useState(false);
  const wsRef = useRef(null);
  const workspaceEndRef = useRef(null);

  // Stream operations
  useEffect(() => {
    if (!chatId) return;

    const cleanup = streamOperations(chatId, (newOperations) => {
      setActiveOperations(newOperations);
    });

    return cleanup; // Close stream on unmount
  }, [chatId]);

  // Load deliverables and listen for updates
  useEffect(() => {
    if (chatId) {
      loadDeliverables();
      setupDeliverablesWebSocket();
    }
    
    return () => {
      closeDeliverablesWebSocket();
    };
  }, [chatId]);

  // Auto-scroll when operations or deliverables change
  useEffect(() => {
    workspaceEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeOperations, deliverables]);

  const setupDeliverablesWebSocket = () => {
    closeDeliverablesWebSocket();

    const wsUrl = `${WS_BASE_URL}/ws/${chatId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.event === 'new_deliverable' || data.event === 'deliverable_update') {
          console.log('New deliverable received in workspace:', data.deliverable);
          loadDeliverables(); // Refresh deliverables list
        }
      } catch (error) {
        console.error('Error parsing deliverables WebSocket message:', error);
      }
    };
  };

  const closeDeliverablesWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const loadDeliverables = async () => {
    if (!chatId) return;
    
    setLoadingDeliverables(true);
    try {
      const deliverablesData = await getDeliverables(chatId);
      console.log('Loaded deliverables in workspace:', deliverablesData);
      setDeliverables(deliverablesData.deliverables || []);
    } catch (error) {
      console.error('Error loading deliverables:', error);
      setDeliverables([]);
    } finally {
      setLoadingDeliverables(false);
    }
  };

  // Function to detect and parse Google Workspace links
  const parseContentForLinks = (content) => {
    if (!content) return null;

    // Pattern to match any Google Workspace link (Docs, Sheets, Slides)
    const googleWorkspacePattern = /(https:\/\/docs\.google\.com\/(document|spreadsheets|presentation)\/[^\s]+)/gi;
    const match = content.match(googleWorkspacePattern);
    
    if (match) {
      return match[0]; // Return the first URL found
    }
    
    return null;
  };

  // Function to get clean title from content
  const getCleanTitle = (content) => {
    if (!content) return 'Untitled Document';
    
    // Remove any Google Workspace URL and get the remaining text as title
    let title = content.replace(/(Google (Doc|Sheet|Slides?):\s*)?https:\/\/docs\.google\.com\/(document|spreadsheets|presentation)\/[^\s]+/gi, '').trim();
    
    // If no title after removing the link, use first line
    if (!title) {
      title = content.split('\n')[0].replace(/^#\s*/, '').trim();
    }
    
    return title || 'Untitled Document';
  };

  // Get Google Workspace type from URL
  const getGoogleWorkspaceType = (url) => {
    if (!url) return null;
    
    if (url.includes('/document/')) return 'Google Doc';
    if (url.includes('/spreadsheets/')) return 'Google Sheet';
    if (url.includes('/presentation/')) return 'Google Slides';
    
    return 'Google Workspace';
  };

  const getStatusIndicator = (status) => {
    switch (status) {
      case 'active': return <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse shadow-sm shadow-green-400/60"></div>;
      case 'waiting': return <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse shadow-sm shadow-yellow-500/60"></div>;
      case 'completed': return <div className="w-1.5 h-1.5 bg-blue-500 rounded-full shadow-sm shadow-blue-500/60"></div>;
      default: return <div className="w-1.5 h-1.5 bg-gray-500 rounded-full"></div>;
    }
  };

  const getStatusTextClass = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'waiting': return 'text-yellow-400';
      case 'completed': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getOperationIcon = (operationType) => {
    switch (operationType) {
      case 'searching': return <Zap className="w-3 h-3 text-yellow-400" />;
      case 'analyzing': return <Brain className="w-3 h-3 text-purple-400" />;
      case 'question_research': return <FileText className="w-3 h-3 text-cyan-400" />;
      case 'composing': return <FileText className="w-3 h-3 text-green-400" />;
      default: return <Activity className="w-3 h-3 text-gray-400" />;
    }
  };

  const getDeliverableTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'report': return 'bg-blue-500/15 text-blue-400 border-blue-500/20';
      case 'analysis': return 'bg-purple-500/15 text-purple-400 border-purple-500/20';
      case 'summary': return 'bg-green-500/15 text-green-400 border-green-500/20';
      case 'research': return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20';
      case 'google doc': return 'bg-orange-500/15 text-orange-400 border-orange-500/20';
      case 'google sheet': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20';
      case 'google slides': return 'bg-red-500/15 text-red-400 border-red-500/20';
      case 'google workspace': return 'bg-orange-500/15 text-orange-400 border-orange-500/20';
      default: return 'bg-gray-500/15 text-gray-400 border-gray-500/20';
    }
  };

  const formatFileSize = (size) => {
    if (!size) return '';
    if (typeof size === 'string' && size.includes('KB')) return size;
    
    const bytes = parseInt(size);
    if (isNaN(bytes)) return size;
    
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] text-gray-100">
      
      {/* Compact Floating Header */}
      <div className="relative p-4 pb-3">
        <div className="bg-[#252526]/90 backdrop-blur-xl rounded-xl border border-gray-700/40 shadow-2xl p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse shadow-lg shadow-blue-500/60"></div>
              <h2 className="text-sm font-semibold text-gray-50 tracking-tight">Agent Workspace</h2>
            </div>
            <div className="flex items-center space-x-1.5 text-xs">
              {activeOperations.length > 0 && (
                <span className="px-2 py-0.5 bg-green-500/15 text-green-400 rounded-md text-xs font-medium border border-green-500/20">
                  {activeOperations.length}
                </span>
              )}
              {deliverables.length > 0 && (
                <span className="px-2 py-0.5 bg-blue-500/15 text-blue-400 rounded-md text-xs font-medium border border-blue-500/20">
                  {deliverables.length}
                </span>
              )}
              {activeOperations.length === 0 && deliverables.length === 0 && (
                <Activity className="w-3.5 h-3.5 text-gray-400" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-5 thin-scrollbar">
        
        {/* Active Operations Section */}
        <div>
          {/* Compact Section Header */}
          <div className="mb-3">
            <div className="inline-block bg-[#252526]/70 backdrop-blur-lg rounded-lg px-3 py-1.5 border border-gray-700/40 shadow-lg">
              <h3 className="text-xs font-medium text-gray-300 uppercase tracking-wider">
                Active Operations
              </h3>
            </div>
          </div>
          
          <div className="space-y-2.5">
            {activeOperations.length > 0 ? (
              activeOperations.map((op) => (
                <div key={op.id} className="group relative">
                  <div className="flex flex-col p-3.5 bg-[#252526]/70 backdrop-blur-lg rounded-xl border border-gray-700/30 shadow-lg transition-all duration-200 hover:shadow-xl hover:border-gray-600/50 hover:scale-[1.01]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2.5">
                        {getOperationIcon(op.operation_type)}
                        {getStatusIndicator(op.status)}
                        <span className={`text-xs font-medium uppercase ${getStatusTextClass(op.status)}`}>
                          {op.status === 'active' ? 'ACTIVE' : op.status?.toUpperCase() || 'WAITING'}
                        </span>
                        {op.timeActive && op.timeActive !== "0m 0s" && (
                          <span className="text-xs text-gray-500">• {op.timeActive}</span>
                        )}
                      </div>
                      {op.status === 'active' && op.progress && (
                        <div className="flex items-center space-x-1.5 text-xs text-gray-400 bg-gray-800/60 px-2 py-1 rounded-md border border-gray-600/30">
                          <Clock className="w-3 h-3" />
                          <span>{op.progress}</span>
                        </div>
                      )}
                    </div>
                    <h4 className="text-sm text-gray-200 font-medium leading-snug mb-1.5">{op.title}</h4>
                    {op.details && (
                      <p className="text-xs text-gray-400 mb-1.5 line-clamp-2">{op.details}</p>
                    )}
                    {op.source && (
                      <p className="text-xs text-blue-400 truncate bg-blue-500/10 px-2 py-1 rounded border border-blue-500/20">{op.source}</p>
                    )}
                  </div>
                  
                  {/* Subtle hover glow effect */}
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-green-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none" />
                </div>
              ))
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 py-10">
                <div className="p-5 bg-[#252526]/70 backdrop-blur-lg rounded-xl mb-3 border border-gray-700/40 shadow-lg">
                  <Activity className="w-7 h-7 text-gray-400" />
                </div>
                <p className="text-sm font-medium mb-1 text-gray-300">No active operations</p>
                <p className="text-xs text-gray-500 max-w-48 leading-relaxed">Operations will appear here when running</p>
              </div>
            )}
          </div>
        </div>

        {/* Deliverables Section */}
        <div>
          {/* Compact Section Header */}
          <div className="mb-3">
            <div className="inline-flex items-center bg-[#252526]/70 backdrop-blur-lg rounded-lg px-3 py-1.5 border border-gray-700/40 shadow-lg space-x-2.5">
              <h3 className="text-xs font-medium text-gray-300 uppercase tracking-wider">
                Research Deliverables
              </h3>
              {loadingDeliverables && (
                <div className="w-3 h-3 border border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              )}
            </div>
          </div>
          
          <div className="space-y-2.5">
            {deliverables.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 py-12">
                <div className="p-5 bg-[#252526]/70 backdrop-blur-lg rounded-xl mb-3 border border-gray-700/40 shadow-lg">
                  <FileText className="w-7 h-7 text-gray-400" />
                </div>
                <p className="text-sm font-medium mb-1 text-gray-300">No deliverables yet</p>
                <p className="text-xs text-gray-500 max-w-48 leading-relaxed">Research results will appear here when completed</p>
              </div>
            ) : (
              deliverables.map((deliverable, index) => {
                // Check both content field and url field for Google Workspace links
                const googleWorkspaceUrl = parseContentForLinks(deliverable.content) || deliverable.url;
                const cleanTitle = deliverable.title || getCleanTitle(deliverable.content);
                const isGoogleWorkspace = !!googleWorkspaceUrl && googleWorkspaceUrl.includes('docs.google.com');
                const workspaceType = getGoogleWorkspaceType(googleWorkspaceUrl);
                
                return (
                  <div key={index} className="group relative">
                    <div className="flex flex-col p-3.5 bg-[#252526]/70 backdrop-blur-lg rounded-xl border border-gray-700/30 hover:border-gray-600/50 shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-[1.01]">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-200 text-sm mb-2 leading-snug">
                            {cleanTitle}
                          </h4>
                          <div className="flex items-center space-x-2 text-xs text-gray-500 mb-2">
                            <span className={`capitalize px-2 py-0.5 rounded-md border font-medium ${getDeliverableTypeColor(isGoogleWorkspace ? workspaceType : deliverable.type)}`}>
                              {isGoogleWorkspace ? workspaceType : (deliverable.type || 'document')}
                            </span>
                            {!isGoogleWorkspace && deliverable.size && (
                              <>
                                <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
                                <span className="font-mono bg-gray-700/50 px-1.5 py-0.5 rounded border border-gray-600/30">
                                  {formatFileSize(deliverable.size)}
                                </span>
                              </>
                            )}
                            <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
                            <span className="text-gray-400">
                              {new Date(deliverable.created).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex space-x-1.5 ml-4">
                          {isGoogleWorkspace ? (
                            <a
                              href={googleWorkspaceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 bg-orange-600/80 hover:bg-orange-500 rounded-lg transition-all duration-200 hover:scale-105 border border-orange-500/30 group/link"
                              title={`Open ${workspaceType}`}
                            >
                              <ExternalLink size={12} className="text-orange-100 group-hover/link:rotate-12 transition-transform duration-200" />
                            </a>
                          ) : (
                            <button
                              onClick={() => {/* Add download logic for non-Google docs if needed */}}
                              className="p-2 bg-blue-600/80 hover:bg-blue-500 rounded-lg transition-all duration-200 hover:scale-105 border border-blue-500/30 opacity-0 group-hover:opacity-100"
                              title="Download"
                            >
                              <Download size={12} className="text-blue-100" />
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {/* Preview content or URL */}
                      {(deliverable.content || deliverable.url) && (
                        <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-700/40 bg-gray-800/30 px-2 py-1.5 rounded border border-gray-700/40">
                          {isGoogleWorkspace ? (
                            <div className="flex items-center space-x-2">
                              <ExternalLink size={10} className="text-orange-400 flex-shrink-0" />
                              <span className="truncate text-orange-300">
                                {googleWorkspaceUrl}
                              </span>
                            </div>
                          ) : (
                            <span className="truncate">
                              {(deliverable.content || '').split('\n')[0].replace(/^#\s*/, '').substring(0, 120)}...
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    
                    {/* Subtle hover glow effect */}
                    <div className={`absolute inset-0 rounded-xl ${isGoogleWorkspace ? 'bg-gradient-to-r from-orange-500/5 to-yellow-500/5' : 'bg-gradient-to-r from-blue-500/5 to-purple-500/5'} opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none`} />
                  </div>
                );
              })
            )}
          </div>
        </div>
        <div ref={workspaceEndRef} />
      </div>
    </div>
  );
};

AgentWorkspace.propTypes = {
  chatId: PropTypes.string.isRequired,
};

export default AgentWorkspace;