import { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle, ListTodo } from 'lucide-react';
import { streamTasks } from '../../services/ResearchDashboard-api.js';

const TasksOrders = ({ chatId }) => {
  const [tasks, setTasks] = useState([]);

  // Stream tasks
  useEffect(() => {
    if (!chatId) {
      console.log("TasksOrders: No chatId provided, skipping stream setup.");
      return;
    }

    console.log("TasksOrders: Attempting to subscribe to tasks stream for chatId:", chatId);

    const cleanup = streamTasks(chatId, (newTasks) => {
      // THIS IS THE KEY LOG:
      console.log("TasksOrders: Received new tasks from stream:", newTasks);
      setTasks(newTasks);
    });

    return () => {
      console.log("TasksOrders: Cleaning up tasks stream for chatId:", chatId);
      cleanup(); // Close stream on unmount
    };
  }, [chatId]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-3 h-3 text-green-400" />;
      case 'in-progress': return <Clock className="w-3 h-3 text-blue-400 animate-pulse" />;
      case 'pending': return <AlertCircle className="w-3 h-3 text-gray-500" />;
      default: return <AlertCircle className="w-3 h-3 text-gray-500" />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'research': return 'text-blue-400';
      case 'research_question': return 'text-cyan-400';
      case 'analysis': return 'text-purple-400';
      case 'planning': return 'text-emerald-400';
      case 'deliverable': return 'text-amber-400';
      case 'synthesis': return 'text-orange-400';
      case 'completion': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getTypeBackgroundColor = (type) => {
    switch (type) {
      case 'research': return 'bg-blue-500/10 border-blue-500/20';
      case 'research_question': return 'bg-cyan-500/10 border-cyan-500/20';
      case 'analysis': return 'bg-purple-500/10 border-purple-500/20';
      case 'planning': return 'bg-emerald-500/10 border-emerald-500/20';
      case 'deliverable': return 'bg-amber-500/10 border-amber-500/20';
      case 'synthesis': return 'bg-orange-500/10 border-orange-500/20';
      case 'completion': return 'bg-green-500/10 border-green-500/20';
      default: return 'bg-gray-500/10 border-gray-500/20';
    }
  };

  const getProgressBar = (task) => {
    const progress = task.progress || 0;
    if (task.status === 'completed') return null;
    if (progress === 0) return null;
    
    return (
      <div className="w-full bg-gray-700/50 rounded-full h-1 mt-2">
        <div 
          className="bg-blue-400 h-1 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    );
  };

  // Count tasks by status
  const completedCount = tasks.filter(task => task.status === 'completed').length;
  const inProgressCount = tasks.filter(task => task.status === 'in-progress').length;
  const pendingCount = tasks.filter(task => task.status === 'pending').length;

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] text-gray-100">
      
      {/* Compact Floating Header */}
      <div className="relative p-4 pb-3">
        <div className="bg-[#252526]/90 backdrop-blur-xl rounded-xl border border-gray-700/40 shadow-2xl p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-lg shadow-emerald-500/60"></div>
              <h2 className="text-sm font-semibold text-gray-50 tracking-tight">Tasks & Orders</h2>
            </div>
            <div className="flex items-center space-x-1.5 text-xs">
              {tasks.length > 0 ? (
                <>
                  {inProgressCount > 0 && (
                    <span className="px-2 py-0.5 bg-blue-500/15 text-blue-400 rounded-md text-xs font-medium border border-blue-500/20">
                      {inProgressCount}
                    </span>
                  )}
                  {completedCount > 0 && (
                    <span className="px-2 py-0.5 bg-green-500/15 text-green-400 rounded-md text-xs font-medium border border-green-500/20">
                      {completedCount}
                    </span>
                  )}
                  {pendingCount > 0 && (
                    <span className="px-2 py-0.5 bg-gray-500/15 text-gray-400 rounded-md text-xs font-medium border border-gray-500/20">
                      {pendingCount}
                    </span>
                  )}
                </>
              ) : (
                <ListTodo className="w-3.5 h-3.5 text-gray-400" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 thin-scrollbar">
        {tasks.length > 0 ? (
          <div className="space-y-2.5">
            {tasks.map((task) => (
              <div key={task.id} className="group relative">
                <div className="flex items-start space-x-3 p-3.5 bg-[#252526]/70 backdrop-blur-lg rounded-xl border border-gray-700/30 shadow-lg hover:border-gray-600/50 transition-all duration-200 hover:shadow-xl hover:bg-[#252526]/90 hover:scale-[1.01]">
                  <div className="mt-0.5 flex-shrink-0">
                    {getStatusIcon(task.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 font-medium leading-snug mb-2 pr-2">
                      {task.title}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`
                          text-xs font-medium uppercase px-2 py-0.5 rounded-md border text-center min-w-0
                          ${getTypeColor(task.type)} ${getTypeBackgroundColor(task.type)}
                        `}>
                          {task.type === 'research_question' ? 'question' : task.type}
                        </span>
                        <span className="w-1 h-1 bg-gray-600 rounded-full flex-shrink-0"></span>
                        <span className="text-xs text-gray-500 capitalize px-2 py-0.5 bg-gray-700/60 rounded-md border border-gray-600/30">
                          {task.status.replace('-', ' ')}
                        </span>
                      </div>
                      {task.question_id && (
                        <span className="text-xs text-gray-400 font-mono bg-gray-700/40 px-1.5 py-0.5 rounded border border-gray-600/30">
                          #{task.question_id}
                        </span>
                      )}
                    </div>
                    {getProgressBar(task)}
                  </div>
                </div>
                
                {/* Subtle hover glow effect */}
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none" />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 py-12">
            <div className="p-5 bg-[#252526]/70 backdrop-blur-lg rounded-xl mb-3 border border-gray-700/40 shadow-lg">
              <ListTodo className="w-7 h-7 text-gray-400" />
            </div>
            <p className="text-sm font-medium mb-1 text-gray-300">No tasks yet</p>
            <p className="text-xs text-gray-500 max-w-48 leading-relaxed">Task progress will appear here when available</p>
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-3 text-xs text-gray-600 space-y-1 bg-gray-800/60 p-2.5 rounded-lg border border-gray-700/40">
                <p className="font-medium text-gray-500">Debug info:</p>
                <p>Tasks length: {tasks.length}</p>
                <p>Chat ID: {chatId || 'none'}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TasksOrders;