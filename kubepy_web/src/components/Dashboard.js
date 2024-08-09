import React, { useState, useEffect } from 'react';

function Dashboard({ username, onLogout }) {
  const [containers, setContainers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Mock API call - replace with actual API call in production
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
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Welcome, {username}</h1>
        <button onClick={onLogout} style={buttonStyle}>Logout</button>
      </div>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search containers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <span>Showing {filteredContainers.length} items</span>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
        <thead>
          <tr style={{ backgroundColor: '#e0e0e0' }}>
            <th style={tableHeaderStyle}>NAME</th>
            <th style={tableHeaderStyle}>IMAGE</th>
            <th style={tableHeaderStyle}>STATUS</th>
            <th style={tableHeaderStyle}>PORTS</th>
            <th style={tableHeaderStyle}>STARTED</th>
            <th style={tableHeaderStyle}>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          {filteredContainers.map((container) => (
            <tr key={container.id} style={{ borderBottom: '1px solid #e0e0e0' }}>
              <td style={tableCellStyle}>{container.name}</td>
              <td style={tableCellStyle}>{container.image}</td>
              <td style={tableCellStyle}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  backgroundColor: container.status === 'Running' ? '#e6f4ea' : '#fce8e6',
                  color: container.status === 'Running' ? '#137333' : '#c5221f'
                }}>
                  {container.status}
                </span>
              </td>
              <td style={tableCellStyle}>{container.ports}</td>
              <td style={tableCellStyle}>{container.started}</td>
              <td style={tableCellStyle}>
                <button style={{...buttonStyle, marginRight: '8px'}}>
                  {container.status === 'Running' ? 'Stop' : 'Start'}
                </button>
                <button style={{...buttonStyle, backgroundColor: '#fce8e6', color: '#c5221f'}}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const tableHeaderStyle = {
  padding: '12px',
  textAlign: 'left',
  fontWeight: 'bold',
};

const tableCellStyle = {
  padding: '12px',
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#4CAF50',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
};

export default Dashboard;