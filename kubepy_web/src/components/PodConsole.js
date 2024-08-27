import React, { useState } from 'react';
import './PodConsole.css';

function PodConsole({ podName }) {
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCommandChange = (e) => {
    setCommand(e.target.value);
  };

  const handleExecuteCommand = async () => {
    setLoading(true);
    setOutput('');
    
    // Obtén el token del localStorage
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`http://207.248.81.113:5000/pods/${podName}/exec`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Incluye el token en los encabezados
        },
        body: JSON.stringify({ command }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setOutput(data.output || 'No output received');
    } catch (error) {
      setOutput(`Error executing command: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pod-console">
      <h2>Pod Terminal - {podName}</h2>
      <textarea
        className="command-input"
        value={command}
        onChange={handleCommandChange}
        placeholder="Enter command here..."
      />
      <button className="execute-button" onClick={handleExecuteCommand} disabled={loading}>
        {loading ? 'Executing...' : 'Execute'}
      </button>
      <pre className="output-console">{output}</pre>
    </div>
  );
}

export default PodConsole;
