import React, { useState } from 'react';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import PodConsole from './components/PodConsole';  // Importa el componente de la consola

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
    return (
      <div>
        <Dashboard username={username} onLogout={handleLogout} />
        <PodConsole />  {/* Aquí se incluye el componente de la consola */}
      </div>
    );
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
