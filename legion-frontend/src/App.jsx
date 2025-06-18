import { useState } from 'react';
import Sidebar from './components/sidebar/Sidebar';
import MainChatArea from './components/chat/MainChatArea';
import ResearchDashboard from './components/research/ResearchDashboard';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showResearch, setShowResearch] = useState(false);
  const [currentChatId, setCurrentChatId] = useState(null);

  const handleChatSelect = (chatId) => {
    setCurrentChatId(chatId);
    setShowResearch(false); // Close research when selecting a chat
  };

  const handleNewChat = (chatId) => {
    setCurrentChatId(chatId);
    setShowResearch(false); // Close research when creating new chat
  };

  const handleOpenResearch = () => {    
    if (!currentChatId) {
      alert('Please select a chat before opening the research dashboard');
      return;
    }
    
    setShowResearch(true);
  };

  // NEW: Handle mission events from MainChatArea
  const handleMissionEvent = (data) => {
    console.log('Mission event received in App:', data);
    
    if (data.event === 'mission_initiated') {
      console.log('Mission initiated - switching to research dashboard');
      setShowResearch(true);
    }
    // Add other mission events if needed later
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar 
        isOpen={sidebarOpen} 
        onHover={(isHovered) => setSidebarOpen(isHovered)}
        currentChatId={currentChatId}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
      />

      <div className="flex-1 h-full">
        {showResearch ? (
          <ResearchDashboard 
            onClose={() => {
              setShowResearch(false);
            }} 
            chatId={currentChatId}
          />
        ) : (
          <MainChatArea 
            sidebarOpen={sidebarOpen} 
            onOpenResearch={handleOpenResearch}
            currentChatId={currentChatId}
            onMissionEvent={handleMissionEvent} // NEW: Pass mission event handler
          />
        )}
      </div>
    </div>
  );
}

export default App;