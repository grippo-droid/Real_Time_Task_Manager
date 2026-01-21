// src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      
      if (token && savedUser) {
        setUser(JSON.parse(savedUser));
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const login = async (email, password) => {
    const response = await authAPI.login({ email, password });
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    
    return userData;
  };

  const signup = async (username, email, password, role = 'team_member') => {
    try {
      console.log('🔵 Attempting signup...'); // Debug
      const response = await authAPI.signup({ username, email, password, role });
      console.log('✅ Signup response:', response); // Debug
      
      const { access_token, user: userData } = response.data;
      
      if (!access_token || !userData) {
        throw new Error('Invalid response format from server');
      }
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      return userData;
    } catch (error) {
      console.error('❌ Signup error:', error);
      console.error('❌ Error response:', error.response?.data);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const isAdmin = () => user?.role === 'admin';
  const isManager = () => user?.role === 'team_manager' || user?.role === 'admin';
  const isMember = () => user?.role === 'team_member';

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAdmin,
    isManager,
    isMember,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};