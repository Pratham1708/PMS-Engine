import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('pms_authenticated') === 'true';
  });

  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('pms_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (credentials) => {
    const mockUser = {
      name: credentials.email ? credentials.email.split('@')[0] : 'Quant Analyst',
      email: credentials.email || 'analyst@pmsengine.com',
      role: 'Institutional Researcher',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'
    };
    setIsAuthenticated(true);
    setUser(mockUser);
    localStorage.setItem('pms_authenticated', 'true');
    localStorage.setItem('pms_user', JSON.stringify(mockUser));
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('pms_authenticated');
    localStorage.removeItem('pms_user');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
