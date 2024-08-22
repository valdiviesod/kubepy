import React, { useState, useEffect } from 'react';
import './Dashboard.css';

function Dashboard({ username, onLogout }) {
  const [pods, setPods] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Simulated API call
    const mockPods = [
      { id: 1, name: 'Nginx Proyecto 1', image: 'nginxlatest', ports: '80,443', podIp: '192.168.0.20', status: 'Active' },
      { id: 2, name: 'Pod 2', image: 'image2', ports: '8080', podIp: '192.168.0.21', status: 'Inactive' },
      { id: 3, name: 'Pod 3', image: 'image3', ports: '3000', podIp: '192.168.0.22', status: 'Active' },
    ];
    setPods(mockPods);
  }, []);

  const filteredPods = pods.filter(pod =>
    pod.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="logo">UPB</div>
        <h1>Hello, User 👋</h1>
      </div>
      <div className="dashboard-content">
        <h2>My Pods</h2>
        <div className="pod-controls">
          <button className="new-pod-button">New Pod</button>
          <input
            type="text"
            placeholder="Search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select>
            <option>Sort by: Latest</option>
          </select>
        </div>
        <table className="pod-table">
          <thead>
            <tr>
              <th>Pod Name</th>
              <th>Image</th>
              <th>Ports</th>
              <th>Pod IP</th>
              <th>Modify</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredPods.map((pod) => (
              <tr key={pod.id}>
                <td>{pod.name}</td>
                <td>{pod.image}</td>
                <td>{pod.ports}</td>
                <td>{pod.podIp}</td>
                <td>
                  <button className="icon-button settings-button"></button>
                  <button className="icon-button delete-button"></button>
                </td>
                <td>
                  <span className={`status-badge ${pod.status.toLowerCase()}`}>
                    {pod.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="pagination">
          <span>Showing data 1 to 8 of 256K entries</span>
          <div className="page-numbers">
            <button className="page-button active">1</button>
            <button className="page-button">2</button>
            <button className="page-button">3</button>
            <button className="page-button">4</button>
            <span>...</span>
            <button className="page-button">40</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;