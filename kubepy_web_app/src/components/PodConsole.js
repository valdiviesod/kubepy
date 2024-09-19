import React, { useState } from 'react';
import './PodConsole.css';

function PodConsole({ podName, onClose }) {
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCommandChange = (e) => {
    setCommand(e.target.value);
  };

  const handleExecuteCommand = async () => {
    setLoading(true);
    setOutput('');

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`https://cca.bucaramanga.upb.edu.co:5000/pods/${podName}/exec`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
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
    <div className="pod-console-container">
      <div className="console-header">
        <h2>Web terminal</h2>
        <button className="close-button" onClick={onClose}>X</button>
      </div>
      <div className="console-body">
        <div className="command-output">{output}</div>
        <div className="command-input-container">
          <span className="prompt">$</span>
          <input
            type="text"
            className="command-input"
            value={command}
            onChange={handleCommandChange}
            onKeyPress={(e) => e.key === 'Enter' && handleExecuteCommand()}
            placeholder="Enter command..."
          />
        </div>
      </div>
    </div>
  );
}

export default PodConsole;
