import React, { useState } from 'react';

function Login({ onLoginSuccess, onRegisterClick }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically make an API call to verify credentials
    // For now, we'll just simulate a successful login
    onLoginSuccess(username);
  };

  return (
    <form onSubmit={handleSubmit} style={formStyle}>
      <h2>Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={inputStyle}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={inputStyle}
      />
      <button type="submit" style={buttonStyle}>Login</button>
      <p style={registerLinkStyle}>
        Don't have an account? <span onClick={onRegisterClick} style={linkStyle}>Register</span>
      </p>
    </form>
  );
}

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
  maxWidth: '300px',
  margin: '0 auto',
};

const inputStyle = {
  margin: '10px 0',
  padding: '8px',
  borderRadius: '4px',
  border: '1px solid #ccc',
};

const buttonStyle = {
  marginTop: '10px',
  padding: '8px 16px',
  backgroundColor: '#4CAF50',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
};

const registerLinkStyle = {
  marginTop: '15px',
  textAlign: 'center',
};

const linkStyle = {
  color: '#4CAF50',
  cursor: 'pointer',
  textDecoration: 'underline',
};

export default Login;