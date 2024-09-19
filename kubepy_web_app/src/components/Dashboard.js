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
        const token = localStorage.getItem('token'); // Obtener el token del localStorage
        const response = await fetch(`https://cca.bucaramanga.upb.edu.co:5000/pods/${podName}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`, // Incluir el token en la cabecera de autorización
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          // Pod eliminado con éxito, actualizar la lista de pods
          setPods(pods.filter(pod => pod.name !== podName));
        } else {
          console.error('Error deleting pod:', response.statusText);
        }
      } catch (error) {
        console.error('Error deleting pod:', error);
      }
    }
  };

  useEffect(() => {
    // Función para cargar los pods desde la API
    const fetchPods = async () => {
      try {
        const token = localStorage.getItem('token'); // Obtener el token del localStorage
        const response = await fetch('https://cca.bucaramanga.upb.edu.co:5000/pods', {
          headers: {
            'Authorization': `Bearer ${token}`, // Incluir el token en la cabecera de autorización
          },
        });

        if (response.ok) {
          const data = await response.json();
          setPods(data); // Actualizar el estado con los pods obtenidos
        } else {
          console.error('Error fetching pods:', response.statusText);
        }
      } catch (error) {
        console.error('Error fetching pods:', error);
      }
    };

    fetchPods();
  }, []); // Ejecutar una vez al cargar el componente

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
                <tr key={pod.name}>
                  <td>{pod.name}</td>
                  <td>{pod.image}</td>
                  <td>{pod.ports}</td>
                  <td>{pod.ip || 'N/A'}</td> {/* Mostrar IP si está disponible */}
                  <td>
                    <button className="icon-button">⚙️</button>
                    <button className="icon-button" onClick={() => handleDeletePod(pod.name)}>🗑️</button>
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
