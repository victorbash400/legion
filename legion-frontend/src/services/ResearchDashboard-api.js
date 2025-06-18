// research-api.js - Enhanced with deliverables and mission completion
const CHAT_API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';
const RESEARCH_API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

// Stream tasks for a specific chat
export const streamTasks = (chatId, callback) => {
  const eventSource = new EventSource(`${RESEARCH_API_BASE_URL}/research/${chatId}/tasks/stream`);
  
  eventSource.addEventListener('tasks', (event) => {
    try {
      const data = JSON.parse(event.data);
      callback(data);
    } catch (error) {
      console.error('Error parsing tasks data:', error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('Error streaming tasks:', error);
    eventSource.close();
  };

  eventSource.onopen = () => {
    console.log('Tasks stream connected for chat:', chatId);
  };

  return () => {
    console.log('Closing tasks stream for chat:', chatId);
    eventSource.close();
  };
};

// Stream active operations for a specific chat
export const streamOperations = (chatId, callback) => {
  const eventSource = new EventSource(`${RESEARCH_API_BASE_URL}/research/${chatId}/operations/stream`);
  
  eventSource.addEventListener('operations', (event) => {
    try {
      const data = JSON.parse(event.data);
      callback(data);
    } catch (error) {
      console.error('Error parsing operations data:', error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('Error streaming operations:', error);
    eventSource.close();
  };

  eventSource.onopen = () => {
    console.log('Operations stream connected for chat:', chatId);
  };

  return () => {
    console.log('Closing operations stream for chat:', chatId);
    eventSource.close();
  };
};

// Stream agent communications for a specific chat
export const streamAgentComms = (chatId, callback) => {
  const eventSource = new EventSource(`${RESEARCH_API_BASE_URL}/research/${chatId}/comms/stream`);
  
  eventSource.addEventListener('comms', (event) => {
    try {
      const data = JSON.parse(event.data);
      callback(data);
    } catch (error) {
      console.error('Error parsing comms data:', error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('Error streaming agent comms:', error);
    eventSource.close();
  };

  eventSource.onopen = () => {
    console.log('Agent comms stream connected for chat:', chatId);
  };

  return () => {
    console.log('Closing agent comms stream for chat:', chatId);
    eventSource.close();
  };
};

// NEW: Stream deliverables for a specific chat
export const streamDeliverables = (chatId, callback) => {
  const eventSource = new EventSource(`${RESEARCH_API_BASE_URL}/research/${chatId}/deliverables/stream`);
  
  eventSource.addEventListener('deliverables', (event) => {
    try {
      const data = JSON.parse(event.data);
      callback(data);
    } catch (error) {
      console.error('Error parsing deliverables data:', error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('Error streaming deliverables:', error);
    eventSource.close();
  };

  eventSource.onopen = () => {
    console.log('Deliverables stream connected for chat:', chatId);
  };

  return () => {
    console.log('Closing deliverables stream for chat:', chatId);
    eventSource.close();
  };
};

// NEW: WebSocket connection for real-time mission events
export const connectWebSocket = (chatId, onMissionEvent) => {
  const ws = new WebSocket(`${WS_BASE_URL}/ws/${chatId}`);
  
  ws.onopen = () => {
    console.log('WebSocket connected for chat:', chatId);
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('WebSocket message received:', data);
      
      // Handle mission completion and other events
      if (onMissionEvent) {
        onMissionEvent(data);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket closed for chat:', chatId);
  };
  
  return ws;
};

// NEW: Check mission status
export const getMissionStatus = async (chatId) => {
  try {
    const response = await fetch(`${RESEARCH_API_BASE_URL}/research/${chatId}/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching mission status:', error);
    throw error;
  }
};

// Optional: Non-streaming functions to get current data
export const getCurrentTasks = async (chatId) => {
  try {
    const response = await fetch(`${RESEARCH_API_BASE_URL}/research/${chatId}/tasks`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching current tasks:', error);
    throw error;
  }
};

export const getCurrentOperations = async (chatId) => {
  try {
    const response = await fetch(`${RESEARCH_API_BASE_URL}/research/${chatId}/operations`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching current operations:', error);
    throw error;
  }
};

export const getCurrentComms = async (chatId) => {
  try {
    const response = await fetch(`${RESEARCH_API_BASE_URL}/research/${chatId}/comms`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching current comms:', error);
    throw error;
  }
};

// NEW: Get current deliverables
export const getCurrentDeliverables = async (chatId) => {
  try {
    const response = await fetch(`${RESEARCH_API_BASE_URL}/research/${chatId}/deliverables`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching current deliverables:', error);
    throw error;
  }
};