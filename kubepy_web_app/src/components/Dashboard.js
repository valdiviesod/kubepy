import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import PodConsole from './PodConsole';

function Dashboard({ onLogout }) {
  const [pods, setPods] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPod, setSelectedPod] = useState(null);

  const handleDeletePod = async (podName) => {
    const isConfirmed = window.confirm(`Are you sure you want to delete the pod "${podName}"?`);

    if (isConfirmed) {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`https://cca.bucaramanga.upb.edu.co:5000/pods/${podName}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          setPods(prevPods => prevPods.filter(pod => pod.name !== podName));
        } else {
          console.error('Error deleting pod:', response.statusText);
        }
      } catch (error) {
        console.error('Error deleting pod:', error);
      }
    }
  };

  useEffect(() => {
    const fetchPods = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('https://cca.bucaramanga.upb.edu.co:5000/pods', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setPods(data.pods); 
        } else {
          console.error('Error fetching pods:', response.statusText);
        }
      } catch (error) {
        console.error('Error fetching pods:', error);
      }
    };

    fetchPods();
  }, []);

  const filteredPods = pods ? pods.filter(pod =>
    pod.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) : [];

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
              Mis Contenedores
            </li>
          </ul>
        </nav>
      </aside>
      <main className="main-content">
        <header className="dashboard-header">
          <h1>Bienvenido 👋</h1>
          <button className="logout-button" onClick={onLogout}>Logout</button>
        </header>
        <div className="dashboard-content">
          <div className="pod-controls">
            <button className="new-pod-button">Nuevo Contenedor</button>
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
                <th>Node Ports</th>
                <th>Modify</th>
                <th>Status</th>
                <th>Terminal</th>
              </tr>
            </thead>
            <tbody>
              {filteredPods.map((pod) => (
                <tr key={pod.name}>
                  <td>{pod.name}</td>
                  <td>{pod.image}</td>
                  <td>{pod.ports}</td>
                  <td>{pod.nodePorts}</td>
                  <td>
                    <button className="icon-button">⚙️</button>
                    <button className="icon-button" onClick={() => handleDeletePod(pod.name)}>🗑️</button>
                  </td>
                  <td>
                    <span className={`status-badge ${pod.status?.toLowerCase()}`}>
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