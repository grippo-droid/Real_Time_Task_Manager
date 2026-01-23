// src/pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tasksAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
  LayoutDashboard, Users, ListTodo, LogOut,
  TrendingUp, Clock, CheckCircle
} from 'lucide-react';
import { ThemeToggle } from '../components/ThemeToggle';
import { Avatar } from '../components/Avatar';
import ActivityFeed from '../components/ActivityFeed';

const Dashboard = () => {
  const { user, logout, isAdmin, isManager } = useAuth();
  const navigate = useNavigate();
  const [boards, setBoards] = useState([]);
  const [myTasks, setMyTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBoards: 0,
    totalTasks: 0,
    completedTasks: 0,
    pendingTasks: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [boardsRes, tasksRes] = await Promise.all([
        tasksAPI.getMyBoards(),
        tasksAPI.getMyTasks()
      ]);

      setBoards(boardsRes.data);
      setMyTasks(tasksRes.data);

      const completed = tasksRes.data.filter(t => t.status === 'completed').length;
      setStats({
        totalBoards: boardsRes.data.length,
        totalTasks: tasksRes.data.length,
        completedTasks: completed,
        pendingTasks: tasksRes.data.length - completed
      });
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const StatCard = ({ icon: Icon, title, value, color }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 dark:text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
        </div>
        <div className={`p-4 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/profile')} className="focus:outline-none">
                <Avatar user={user} size="md" className="ring-2 ring-indigo-100 dark:ring-indigo-900 hover:ring-indigo-300 transition" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Task Manager</h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Welcome back, {user?.username}!
                  <span className="ml-2 px-2 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-200 text-xs rounded-full">
                    {user?.role?.replace('_', ' ')}
                  </span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={LayoutDashboard}
            title="My Boards"
            value={stats.totalBoards}
            color="bg-blue-500"
          />
          <StatCard
            icon={ListTodo}
            title="Total Tasks"
            value={stats.totalTasks}
            color="bg-purple-500"
          />
          <StatCard
            icon={CheckCircle}
            title="Completed"
            value={stats.completedTasks}
            color="bg-green-500"
          />
          <StatCard
            icon={Clock}
            title="Pending"
            value={stats.pendingTasks}
            color="bg-orange-500"
          />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {isAdmin() && (
            <button
              onClick={() => navigate('/admin')}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition"
            >
              <Users className="w-8 h-8 mb-3" />
              <h3 className="text-lg font-semibold">Admin Panel</h3>
              <p className="text-sm text-purple-100 mt-1">Manage teams, boards & users</p>
            </button>
          )}

          {isManager() && (
            <button
              onClick={() => navigate('/manager')}
              className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition"
            >
              <TrendingUp className="w-8 h-8 mb-3" />
              <h3 className="text-lg font-semibold">Task Manager</h3>
              <p className="text-sm text-blue-100 mt-1">Create & manage tasks</p>
            </button>
          )}

          <button
            onClick={() => navigate('/boards')}
            className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition"
          >
            <LayoutDashboard className="w-8 h-8 mb-3" />
            <h3 className="text-lg font-semibold">My Boards</h3>
            <p className="text-sm text-green-100 mt-1">View all your boards</p>
          </button>
        </div>

        {/* My Boards */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">My Boards</h2>
            <button
              onClick={() => navigate('/boards')}
              className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
            >
              View All →
            </button>
          </div>

          {boards.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <LayoutDashboard className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No boards available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {boards.slice(0, 6).map((board) => (
                <button
                  key={board.id}
                  onClick={() => navigate(`/boards/${board.id}`)}
                  className="text-left p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-indigo-500 hover:shadow-md transition"
                >
                  <h3 className="font-semibold text-gray-900 dark:text-white">{board.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {board.description || 'No description'}
                  </p>
                  <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
                    <Users className="w-4 h-4" />
                    {board.member_count} members
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Recent Tasks */}
        {/* Recent Tasks & Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Tasks */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">My Recent Tasks</h2>
              <button
                onClick={() => navigate('/tasks')}
                className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
              >
                View All →
              </button>
            </div>

            {myTasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <ListTodo className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No tasks assigned to you</p>
              </div>
            ) : (
              <div className="space-y-3">
                {myTasks.slice(0, 5).map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-white">{task.title}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {task.description || 'No description'}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${task.status === 'completed' ? 'bg-green-100 text-green-700' :
                        task.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                        {task.status.replace('_', ' ')}
                      </span>
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                        task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                          task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                        }`}>
                        {task.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Activity Feed */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Activity Feed</h2>
            <ActivityFeed />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;