import React, { useState } from 'react';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [username, setUsername] = useState('');

  const handleLogin = (user) => {
    setIsLoggedIn(true);
    setUsername(user);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername('');
  };

  if (isLoggedIn) {
    return <Dashboard username={username} onLogout={handleLogout} />;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ marginBottom: '20px' }}>Kubepy</h1>
      {showRegister ? (
        <Register 
          onRegisterSuccess={() => setShowRegister(false)} 
          onBackToLogin={() => setShowRegister(false)}
        />
      ) : (
        <Login 
          onLoginSuccess={handleLogin} 
          onRegisterClick={() => setShowRegister(true)}
        />
      )}
    </div>
  );
}

export default App;
