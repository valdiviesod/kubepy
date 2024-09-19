import React, { useState } from 'react';
import './Login.css';

function Login({ onLoginSuccess, onRegisterClick }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Limpiar cualquier error previo

    try {
      const response = await fetch('https://cca.bucaramanga.upb.edu.co:5000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.access_token; // Asume que el token se devuelve como { access_token: 'JWT...' }
        localStorage.setItem('token', token); // Almacenar el token en localStorage
        onLoginSuccess(username); // Llamar a onLoginSuccess con el nombre de usuario
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Error en la autenticación');
      }
    } catch (error) {
      setError('Error en la solicitud. Intenta de nuevo.');
      console.error('Error en la solicitud:', error);
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Iniciar Sesión</h2>
        {error && <div className="error-message">{error}</div>}
        <input
          type="text"
          placeholder="Nombre de usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Iniciar Sesión</button>
        <p>No tienes una cuenta? <span onClick={onRegisterClick} style={{ cursor: 'pointer', color: 'blue' }}>Regístrate aquí</span></p>
      </form>
    </div>
  );
}

export default Login;
