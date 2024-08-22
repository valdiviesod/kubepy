import React, { useState, useEffect } from 'react';
import './Dashboard.css';  // Crea un archivo CSS separado para estilos

function Dashboard({ username, onLogout }) {
  const [containers, setContainers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Simulación de API
    const mockContainers = [
      { id: 1, name: 'dockercontext', image: '-', status: 'Running', ports: '-', started: '2 minutes ago' },
      { id: 2, name: 'mysql-db', image: 'mysql:5.7', status: 'Stopped', ports: '3306', started: '1 hour ago' },
      { id: 3, name: 'nginx-server', image: 'nginx:latest', status: 'Running', ports: '80', started: '30 minutes ago' },
    ];
    setContainers(mockContainers);
  }, []);

  const filteredContainers = containers.filter(container =>
    container.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Welcome, {username}</h1>
        <button className="logout-button" onClick={onLogout}>Logout</button>
      </div>
      <div className="dashboard-search">
        <input
          type="text"
          placeholder="Search containers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <span>Showing {filteredContainers.length} items</span>
      </div>
      <table className="dashboard-table">
        <thead>
          <tr>
            <th>NAME</th>
            <th>IMAGE</th>
            <th>STATUS</th>
            <th>PORTS</th>
            <th>STARTED</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          {filteredContainers.map((container) => (
            <tr key={container.id}>
              <td>{container.name}</td>
              <td>{container.image}</td>
              <td>
                <span className={`status-badge ${container.status === 'Running' ? 'running' : 'stopped'}`}>
                  {container.status}
                </span>
              </td>
              <td>{container.ports}</td>
              <td>{container.started}</td>
              <td>
                <button className="action-button start-stop-button">
                  {container.status === 'Running' ? 'Stop' : 'Start'}
                </button>
                <button className="action-button delete-button">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Dashboard;
