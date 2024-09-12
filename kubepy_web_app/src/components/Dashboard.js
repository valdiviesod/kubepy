import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import PodConsole from './PodConsole';

function Dashboard({ onLogout }) {
  const [pods, setPods] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPod, setSelectedPod] = useState(null);

  useEffect(() => {
    const mockPods = [
      { id: 1, name: 'test1', image: 'nginxlatest', ports: '80,443', status: 'Inactive' },
      { id: 2, name: 'test2', image: 'image2', ports: '8080', status: 'Inactive' },
      { id: 3, name: 'Pod 3', image: 'image3', ports: '3000', status: 'Active' },
    ];
    setPods(mockPods);
  }, []);

  const filteredPods = pods.filter(pod => 
    pod.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleOpenTerminal = (podName) => {
    setSelectedPod(podName);
  };

  const handleCloseTerminal = () => {
    setSelectedPod(null); 
  };

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <div className="logo">UPB</div>
        <nav>
          <ul>
            <li className="active">
              <span className="icon">📦</span>
              My Pods
            </li>
          </ul>
        </nav>
      </aside>
      <main className="main-content">
        <header className="dashboard-header">
          <h1>Hello, 👋</h1>
          <button className="logout-button" onClick={onLogout}>Logout</button>
        </header>
        <div className="dashboard-content">
          <div className="pod-controls">
            <h2>My Pods</h2>
            <button className="new-pod-button">New Pod</button>
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
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
                <th>Terminal</th>
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
                    <button className="icon-button">⚙️</button>
                    <button className="icon-button">🗑️</button>
                  </td>
                  <td>
                    <span className={`status-badge ${pod.status.toLowerCase()}`}>
                      {pod.status}
                    </span>
                  </td>
                  <td>
                    <button className="terminal-button" onClick={() => handleOpenTerminal(pod.name)}>🖥️ Open Terminal</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <div className="page-numbers">
              <button className="page-button active">1</button>
              <button className="page-button">2</button>
              <button className="page-button">3</button>
              <button className="page-button">4</button>
              <button className="page-button">...</button>
              <button className="page-button">48</button>
            </div>
          </div>
        </div>
      </main>
      {selectedPod && (
        <PodConsole podName={selectedPod} onClose={handleCloseTerminal} />
      )}
    </div>
  );
}

export default Dashboard;
