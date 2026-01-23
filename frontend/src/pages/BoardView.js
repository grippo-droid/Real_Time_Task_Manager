// src/pages/BoardView.js
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tasksAPI, chatAPI } from '../services/api';
import toast from 'react-hot-toast';
import { ArrowLeft, Send, Users, MessageCircle, CheckCircle } from 'lucide-react';
import { KanbanBoard } from '../components/kanban/KanbanBoard';
import { ThemeToggle } from '../components/ThemeToggle';

const BoardView = () => {
  const { boardId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [ws, setWs] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadBoards();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (boardId) {
      loadBoardData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boardId]);

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadBoards = async () => {
    try {
      const response = await tasksAPI.getMyBoards();
      if (!boardId && response.data.length > 0) {
        navigate(`/boards/${response.data[0].id}`);
      }
    } catch (error) {
      toast.error('Failed to load boards');
    } finally {
      setLoading(false);
    }
  };

  const loadBoardData = async () => {
    try {
      const [boardRes, tasksRes] = await Promise.all([
        tasksAPI.getBoardDetails(boardId),
        tasksAPI.getBoardTasks(boardId)
      ]);
      setBoard(boardRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      toast.error('Failed to load board data');
    }
  };

  const connectToChat = () => {
    const token = localStorage.getItem('token');
    const websocket = chatAPI.connectToBoard(boardId, token);

    websocket.onopen = () => {
      console.log('Connected to chat');
      toast.success('Connected to board chat');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'chat') {
        setMessages(prev => [...prev, data]);
      } else if (data.type === 'system') {
        setMessages(prev => [...prev, data]);
      } else if (data.type === 'user_joined') {
        setMessages(prev => [...prev, {
          type: 'system',
          message: `${data.username} joined the chat`,
          timestamp: data.timestamp
        }]);
        loadOnlineUsers();
      } else if (data.type === 'user_left') {
        setMessages(prev => [...prev, {
          type: 'system',
          message: `${data.username} left the chat`,
          timestamp: data.timestamp
        }]);
        loadOnlineUsers();
      } else if (data.type === 'task_update') {
        setMessages(prev => [...prev, {
          type: 'system',
          message: `${data.username} ${data.action} a task`,
          timestamp: data.timestamp
        }]);
        loadBoardData();
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Chat connection error');
    };

    websocket.onclose = () => {
      console.log('Disconnected from chat');
    };

    setWs(websocket);
    loadOnlineUsers();
  };

  const loadOnlineUsers = async () => {
    try {
      const response = await chatAPI.getOnlineUsers(boardId);
      setOnlineUsers(response.data.online_users);
    } catch (error) {
      console.error('Failed to load online users');
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !ws) return;

    ws.send(JSON.stringify({
      type: 'chat',
      message: newMessage
    }));

    setNewMessage('');
  };

  const handleTaskStatusUpdate = async (taskId, newStatus) => {
    try {
      await tasksAPI.updateTaskStatus(taskId, newStatus);
      toast.success('Task status updated');
      loadBoardData();

      // Notify via WebSocket
      if (ws) {
        ws.send(JSON.stringify({
          type: 'task_update',
          task_id: taskId,
          action: 'updated',
          details: { status: newStatus }
        }));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };



  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{board?.name || 'Board'}</h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{board?.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <button
                  onClick={() => {
                    setShowChat(!showChat);
                    if (!showChat && !ws) {
                      connectToChat();
                    }
                  }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${showChat
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  <MessageCircle className="w-5 h-5" />
                  Chat {onlineUsers.length > 0 && `(${onlineUsers.length})`}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Board Stats */}
        {board && (
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span>{board.member_ids?.length || 0} members</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>{board.stats?.total_tasks || 0} tasks</span>
              </div>
              <div>
                <span className="text-green-600 font-medium">
                  {board.stats?.completed_tasks || 0} completed
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Kanban Board */}
        <KanbanBoard
          tasks={tasks}
          onTaskDrop={handleTaskStatusUpdate}
          currentUserId={user.id}
        />
      </div>

      {/* Chat Sidebar */}
      {showChat && (
        <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Board Chat</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {onlineUsers.length} {onlineUsers.length === 1 ? 'person' : 'people'} online
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx}>
                {msg.type === 'system' ? (
                  <div className="text-center text-xs text-gray-500 py-2">
                    {msg.message}
                  </div>
                ) : (
                  <div className={`flex ${msg.user_id === user.id ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs rounded-lg px-4 py-2 ${msg.user_id === user.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                      }`}>
                      {msg.user_id !== user.id && (
                        <p className="text-xs font-semibold mb-1">{msg.username}</p>
                      )}
                      <p className="text-sm">{msg.message}</p>
                      <p className={`text-xs mt-1 ${msg.user_id === user.id ? 'text-indigo-200' : 'text-gray-500'
                        }`}>
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white"
              />
              <button
                type="submit"
                disabled={!newMessage.trim()}
                className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default BoardView;